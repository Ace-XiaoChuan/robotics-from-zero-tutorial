"""用 Pinocchio CLIK 控制 Franka Panda 末端到达目标位姿。

这个脚本对应计划的 IK/CLIK 学习目标：

1. MuJoCo 提供仿真状态和 viewer。
2. Pinocchio 从 URDF 建立运动学模型。
3. CLIK 根据末端位姿误差和 Jacobian 迭代求关节目标。
4. MuJoCo 的 position actuator 接收关节目标，让机械臂移动。

推荐运行方式：

    /home/ace/mujoco-env/bin/python src/lesson9/control_ee_with_pinocchio.py
"""

import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.linalg import norm, solve

try:
    import mujoco
    import mujoco.viewer
    import pinocchio as pin
except ModuleNotFoundError as exc:
    raise ModuleNotFoundError(
        f"缺少 Python 包 {exc.name!r}。请用 /home/ace/mujoco-env/bin/python "
        "运行这个 lesson；系统 Python 通常找不到 mujoco/pinocchio。"
    ) from exc


# 和 check_fk_with_mujoco.py 保持一致：模型文件和辅助项目都在外部 mujoco-learning 中。
# 不再使用相对路径 model/...，避免脚本从不同 cwd 运行时找不到模型。
MUJOCO_LEARNING_ROOT = Path("~/litchi_tutorial/mujoco-learning").expanduser()
SCENE_XML_PATH = MUJOCO_LEARNING_ROOT / "model/franka_emika_panda/scene_pos.xml"
URDF_PATH = MUJOCO_LEARNING_ROOT / "model/franka_panda_urdf/robots/panda_arm.urdf"

# 这个 URDF 只有 7 个机械臂关节；MuJoCo scene 里还有 2 个夹爪 qpos。
ARM_DOF = 7

# 使用 ee_center_body 做 IK 和 MuJoCo 检查，避免“求的是 link7，看的却是手爪中心”的错位。
EE_FRAME_NAME = "ee_center_body"


@dataclass
class IkResult:
    """一次 IK 求解的结果，方便在日志里记录成功/失败和误差。"""

    q: np.ndarray
    success: bool
    iterations: int
    error: np.ndarray
    position_error: float
    rotation_error: float
    reason: str


def require_file(path, label):
    """运行前检查模型路径，报错时直接指出应该检查哪里。"""
    if not path.exists():
        raise FileNotFoundError(
            f"找不到 {label}: {path}\n"
            f"请确认 MUJOCO_LEARNING_ROOT 是否正确: {MUJOCO_LEARNING_ROOT}"
        )


class PinocchioClik:
    """基于 Pinocchio 的 closed-loop inverse kinematics。

    CLIK 的核心不是一次性求解析解，而是在当前 q 附近用 Jacobian 做局部线性近似，
    反复把末端误差变成关节速度，再积分成新的关节位置。
    """

    def __init__(
        self,
        urdf_path,  # Pinocchio 建模用的机械臂 URDF 路径。
        ee_frame_name,  # IK/FK 使用的末端 frame 名称。
        eps=1e-4,  # 6 维位姿误差的收敛阈值。
        max_iterations=120,  # 每次 IK 求解允许的最大迭代次数。
        integration_step=0.1,  # 把关节速度积分成关节位置时的步长。
        damping=1e-6,  # 阻尼最小二乘里的阻尼系数，奇异位形附近更稳定。
    ):
        require_file(urdf_path, "Panda URDF")
        self.model = pin.buildModelFromUrdf(str(urdf_path))
        self.data = self.model.createData()
        self.ee_frame_name = ee_frame_name
        self.ee_frame_id = self.model.getFrameId(ee_frame_name)
        if self.ee_frame_id == self.model.nframes:
            raise ValueError(f"Pinocchio frame not found: {ee_frame_name}")

        self.eps = eps
        self.max_iterations = max_iterations
        self.integration_step = integration_step
        self.damping = damping

    def _to_pin_q(self, q):
        """把 MuJoCo qpos 或普通列表整理成 Pinocchio 期望的 7 维 q。"""
        q = np.asarray(q, dtype=np.float64)
        q_pin = np.zeros(self.model.nq, dtype=np.float64)
        q_pin[: min(q.size, self.model.nq)] = q[: min(q.size, self.model.nq)]
        return q_pin

    def fk(self, q):
        """返回末端 frame 在世界坐标系下的 Pinocchio SE3 位姿。"""
        q_pin = self._to_pin_q(q)
        pin.forwardKinematics(self.model, self.data, q_pin)
        # FK 只更新关节树；这里再刷新各个 frame 的世界位姿缓存。
        pin.updateFramePlacements(self.model, self.data)
        # oMf 存的是每个 frame 在世界坐标系下的位姿；这里取末端 frame 的那一项。
        placement = self.data.oMf[self.ee_frame_id]
        # copy() 不是因为数据量大，而是为了返回一个独立的末端位姿快照。
        return pin.SE3(placement.rotation.copy(), placement.translation.copy())

    def solve(self, current_q, target_pose):
        """从当前关节位置出发，迭代求一个能到达 target_pose 的关节目标。

        这一段是 CLIK 主循环：
        1. 用当前 q 做 FK，得到当前末端位姿。
        2. 计算当前末端到目标末端的 6 维误差。
        3. 用 Jacobian 把末端误差换成关节速度。
        4. 积分得到下一轮 q，并裁剪到关节限位内。
        """
        # q 是 IK 的迭代变量；每一轮都会根据末端误差更新它。
        q = self._to_pin_q(current_q)
        # 从 Pinocchio 模型里取关节位置限制：lower[i] <= q[i] <= upper[i]。
        lower = self.model.lowerPositionLimit
        upper = self.model.upperPositionLimit

        # 记录本次 IK 过程中是否曾经尝试越过关节限位；最后用于解释失败原因。
        touched_joint_limit = False
        # 默认认为是迭代次数用完；后面会根据收敛、奇异或触限情况改写。
        reason = "max_iterations"
        # 先给误差变量一个默认值，保证即使提前失败也能返回可读日志。
        err = np.zeros(6, dtype=np.float64)
        # inf 是 infinity，表示“正无穷大”。进入 IK 循环后，它们会被真实误差覆盖。
        position_error = np.inf
        rotation_error = np.inf

        # 每一轮都围绕当前 q 重新计算 FK、误差和 Jacobian，再更新 q。
        # iteration：迭代
        for iteration in range(self.max_iterations + 1):
            pin.forwardKinematics(self.model, self.data, q)
            # FK 只更新关节树；这里再刷新各个 frame 的世界位姿缓存。
            pin.updateFramePlacements(self.model, self.data)

            current_pose = self.data.oMf[self.ee_frame_id]

            # actInv 的结果可以理解为“从当前末端坐标系看，目标还差多少变换”。返回值类型是：pin.SE3。
            # log(SE3) 再把这个位姿差变成 6 维运动误差向量：前三维近似平移，后三维是旋转误差。
            # log() 是 李群里的 log 映射，可以理解成“广义版对数”。
            current_to_target = current_pose.actInv(target_pose) # 一个 SE3
            err = pin.log(current_to_target).vector # se3

            # 欧氏距离
            # .translation 返回该位姿的平移向量，通常就是[x,y,z],相当于：
            # dx = target_x - current_x
            # dy = target_y - current_y
            # dz = target_z - current_z
            # position_error = sqrt(dx**2 + dy**2 + dz**2)
            position_error = norm(target_pose.translation - current_pose.translation)
            # 位置误差的范数是“两点之间的距离”；姿态误差的范数是“两个姿态之间还需要旋转的角度大小”。
            # 根号下0.3平方+0.4平方+0平方 = 0.5 rad，0.5 rad ≈ 28.65°
            rotation_error = norm(err[3:]) # norm()：求范数。

            # 误差已经足够小，说明当前 q 可以作为 IK 成功结果返回。
            if norm(err) < self.eps:
                reason = "converged" # 已收敛
                return IkResult(
                    q=q,
                    success=True,
                    iterations=iteration,
                    error=err,
                    position_error=position_error,
                    rotation_error=rotation_error,
                    reason=reason,
                )

            # computeFrameJacobian(..., LOCAL) 得到的是末端局部坐标系下的 Jacobian。
            # 因为上面的 err 也是从当前末端坐标系看目标误差，所以这里保持坐标系一致。
            # https://gepettoweb.laas.fr/doc/stack-of-tasks/pinocchio/master/doxygen-html/namespacepinocchio.html#a7b1189aea93a252f4c06d9a7e3c9f5e7
            jacobian = pin.computeFrameJacobian(
                self.model,
                self.data,
                q,
                self.ee_frame_id,
                pin.ReferenceFrame.LOCAL,
            )

            # SE3 的 log 不是简单的 xyz 差值，Jlog6 用来把 Jacobian 映射到和 log(err)
            # 一致的李代数空间；少了这一步，姿态误差较大时更新方向会不稳定。
            # 这行它不是在“重新计算末端 Jacobian”，而是把刚才算出来的 末端运动 Jacobian 转换成 误差 Jacobian。
            # jacobian 是：关节动一点 dq -> 当前末端 dx 自己会怎么动
            # 但是 IK 求解真正需要的是：关节动一点 dq -> err 这个误差会怎么变化
            # 所以1.负号本质上就是：当前末端朝目标移动，误差应该下降，而不是上升。
            # 2.current_to_target.inverse() 是什么：
            # 就是反过来：从目标回到当前
            jacobian = -pin.Jlog6(current_to_target.inverse()) @ jacobian

            try:
                # 阻尼最小二乘：v = -J^T (J J^T + lambda I)^-1 err。
                # damping 越大越不容易在奇异位形爆炸，但也会让收敛变慢。
                joint_velocity = -jacobian.T @ solve(
                    jacobian @ jacobian.T + self.damping * np.eye(6),
                    err,
                )
            except np.linalg.LinAlgError:
                reason = "singular_jacobian"
                break

            # pin.integrate 对 revolute joint 等价于 q + v * dt；用它是为了和
            # Pinocchio 的广义位置接口保持一致，以后换成四元数/free-flyer 也不容易错。
            next_q = pin.integrate(self.model, q, joint_velocity * self.integration_step)

            # Pinocchio 不会自动替你处理关节限位。这里先做最小处理：裁剪并记录，
            # 后续如果要更严格，可以把限位作为优化约束，而不是在积分后硬裁剪。
            clipped_q = np.clip(next_q, lower, upper)
            if not np.allclose(clipped_q, next_q):
                touched_joint_limit = True
            # 用裁剪后的 q 进入下一轮，避免继续从非法关节位置迭代。
            q = clipped_q

        # 如果最后没有收敛，而且过程中触碰过关节限位，就把失败原因说清楚。
        if touched_joint_limit and reason == "max_iterations":
            reason = "max_iterations_or_joint_limit"

        return IkResult(
            q=q,
            success=False,
            iterations=self.max_iterations,
            error=err,
            position_error=position_error,
            rotation_error=rotation_error,
            reason=reason,
        )


class PandaClikViewer:
    """MuJoCo viewer 中的末端位姿闭环 demo。"""

    def __init__(self, scene_xml_path, ik_solver):
        require_file(scene_xml_path, "MuJoCo scene XML")
        self.model = mujoco.MjModel.from_xml_path(str(scene_xml_path))
        self.data = mujoco.MjData(self.model)
        self.ik_solver = ik_solver
        self.handle = None
        self.frame_count = 0  # 当前仿真帧计数，用于生成目标轨迹和控制打印频率。
        self.print_interval = 30
        self.motion_frames = 300  # 末端从起点插值到目标点所需的总帧数。

        self.ee_body_id = mujoco.mj_name2id(
            self.model,
            mujoco.mjtObj.mjOBJ_BODY,
            self.ik_solver.ee_frame_name,
        )
        if self.ee_body_id == -1:
            raise ValueError(f"MuJoCo body not found: {self.ik_solver.ee_frame_name}")

    def reset_to_home(self):
        """使用 MJCF 里的 home keyframe 初始化 MuJoCo 状态。"""
        # keyframe（关键帧）数量
        if self.model.nkey > 0:
            self.data.qpos[:] = self.model.key_qpos[0]
            # nu 对应各个可控关节或电机
            if self.model.nu > 0:
                self.data.ctrl[:] = self.model.key_ctrl[0]
        else:
            self.data.qpos[:] = 0.0

        # position actuator 的 ctrl 是关节目标。把前 7 个 ctrl 设成当前 qpos，
        # 否则仿真一开始可能会被 XML 里的旧 ctrl 拉向另一个位置。
        if self.model.nu >= ARM_DOF:
            self.data.ctrl[:ARM_DOF] = self.data.qpos[:ARM_DOF]

        # 重新计算所有派生物理量，但不推进时间。
        mujoco.mj_forward(self.model, self.data)

        start_pose = self.ik_solver.fk(self.data.qpos[:ARM_DOF])
        self.start_position = start_pose.translation.copy()
        self.target_rotation = start_pose.rotation.copy()

        # 选择一个相对 home 位姿的小范围目标，目的是稳定演示 CLIK。
        # 如果直接给很远的目标，失败可能来自不可达或关节限位，而不是代码本身。
        self.end_position = self.start_position + np.array([-0.20, 0.15, -0.05])

        print("Initial qpos[:7]:", np.round(self.data.qpos[:ARM_DOF], 4))
        print("IK/MuJoCo target frame:", self.ik_solver.ee_frame_name)
        print("Start ee position:", np.round(self.start_position, 4))
        print("Goal ee position:", np.round(self.end_position, 4))

    def target_pose_for_frame(self):
        """按帧数生成一个从起点到终点的末端目标位姿。"""
        alpha = min(1.0, self.frame_count / self.motion_frames)
        target_position = (1.0 - alpha) * self.start_position + alpha * self.end_position
        return pin.SE3(self.target_rotation, target_position)

    def mujoco_ee_pose(self):
        """读取 MuJoCo 中末端 body 的世界位姿，用于和目标位姿做误差记录。"""
        body = self.data.body(self.ee_body_id)
        rotation = body.xmat.reshape(3, 3).copy()
        translation = body.xpos.copy()
        return pin.SE3(rotation, translation)

    def apply_joint_target(self, q_target):
        """把 IK 输出的 7 维关节目标写入 MuJoCo 控制接口。"""
        if self.model.nu >= ARM_DOF:
            self.data.ctrl[:ARM_DOF] = q_target[:ARM_DOF]
        else:
            # 兜底路径：如果 XML 没有 actuator，就只能直接写 qpos，作为纯运动学演示。
            self.data.qpos[:ARM_DOF] = q_target[:ARM_DOF]

    def print_status(self, target_pose, ik_result):
        """记录目标、实际、误差和 IK 状态，满足误差检查要求。"""
        actual_pose = self.mujoco_ee_pose()
        actual_to_target = actual_pose.actInv(target_pose)
        pose_error = pin.log(actual_to_target).vector
        position_error = norm(target_pose.translation - actual_pose.translation)
        rotation_error = norm(pose_error[3:])
        print(
            "frame="
            f"{self.frame_count:04d} "
            f"target={np.round(target_pose.translation, 4)} "
            f"actual={np.round(actual_pose.translation, 4)} "
            f"pos_err={position_error:.5f} "
            f"rot_err={rotation_error:.5f} "
            f"ik_iter={ik_result.iterations} "
            f"ik_reason={ik_result.reason}"
        )

    def run_loop(self):
        """启动 viewer，并在每个仿真步里执行一次 CLIK 控制。"""
        self.model.opt.timestep = 0.005
        self.reset_to_home()
        self.handle = mujoco.viewer.launch_passive(self.model, self.data)
        self.handle.cam.distance = 3
        self.handle.cam.azimuth = 0
        self.handle.cam.elevation = -30

        while self.handle.is_running():
            mujoco.mj_forward(self.model, self.data)
            target_pose = self.target_pose_for_frame()

            # 这里用 MuJoCo 当前 qpos 作为 IK 初值，而不是固定 initial_q。
            # 这样仿真状态、FK、IK、控制目标形成真正的闭环数据流。
            ik_result = self.ik_solver.solve(self.data.qpos[:ARM_DOF], target_pose)
            if ik_result.success:
                self.apply_joint_target(ik_result.q)
            else:
                # 失败时保持当前关节目标，并打印 reason。这样不会把明显失败的 q
                # 当成正常控制量继续送进仿真。
                self.apply_joint_target(self.data.qpos[:ARM_DOF])
                print(
                    "IK failed: "
                    f"reason={ik_result.reason}, "
                    f"pos_err={ik_result.position_error:.5f}, "
                    f"rot_err={ik_result.rotation_error:.5f}"
                )

            if self.frame_count % self.print_interval == 0:
                self.print_status(target_pose, ik_result)

            mujoco.mj_step(self.model, self.data)
            self.handle.sync()
            self.frame_count += 1
            time.sleep(self.model.opt.timestep)


def main():
    ik_solver = PinocchioClik(URDF_PATH, EE_FRAME_NAME)
    viewer = PandaClikViewer(SCENE_XML_PATH, ik_solver)
    viewer.run_loop()


if __name__ == "__main__":
    main()
