"""完成一个最小但可解释的 Panda 机械臂 reaching 闭环，证明已经把 FK、IK、Jacobian 和 MuJoCo 控制接口串起来。这个里程碑只验收运动学和末端位姿闭环。

闭环数据流如下：

MuJoCo data.qpos
   -> Pinocchio / KDL FK
   -> 当前末端位姿
   -> 目标末端位姿误差
   -> Jacobian / CLIK 求关节目标
   -> MuJoCo ctrl 或 qpos 更新
   -> 读取实际末端位姿并计算误差

最低实现要求：

 - FK 对齐：从同一组 `qpos` 出发，对比 MuJoCo body / site 位姿和 Pinocchio FK 结果，位置误差需要可打印、可解释。
 - IK 求解：给定一个目标末端位姿，使用 Pinocchio CLIK 或等价 Jacobian 方法求出 7 维机械臂关节目标。
 - 闭环执行：把 IK 输出写入 MuJoCo 控制接口，让末端从初始位姿移动到目标位姿。
 - 误差记录：每隔固定帧数打印目标位置、实际位置、位置误差、姿态误差、IK 迭代次数和求解状态。

"""

import time
import sys
from pathlib import Path
from dataclasses import dataclass

import numpy as np
import pinocchio as pin
from numpy.linalg import norm, solve

MUJOCO_LEARNING_ROOT = Path("~/litchi_tutorial/mujoco-learning").expanduser()
URDF_PATH = MUJOCO_LEARNING_ROOT / "model/franka_panda_urdf/robots/panda_arm.urdf"
SCENE_XML_PATH = MUJOCO_LEARNING_ROOT / "model/franka_emika_panda/scene_pos.xml"
ARM_XML_PATH = MUJOCO_LEARNING_ROOT / "model/franka_emika_panda/panda_pos.xml"

ARM_DOF = 7

EE_FRAME_NAME = "ee_center_body"

try:
    import mujoco
    import mujoco.viewer
    import pinocchio as pin
except ModuleNotFoundError as exc:
    if exc.name != "mujoco_learning" or not MUJOCO_LEARNING_ROOT.exists():
        raise
    sys.path.insert(0, str(MUJOCO_LEARNING_ROOT))
    from mujoco_learning import kdl_kinematic, mujoco_viewer

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
    

class PinocchioFk:
    """FK 类：由 q 求解末端位姿，当前返回的是 SE(3) 的矩阵表示，不是 pin.SE3 对象。"""
    def __init__(self,ee_frame):
        """记录要查询的末端 frame 名字。

        Args:
            ee_frame: Pinocchio 模型里的末端 frame 名字，例如 "link7"。
        """
        self.ee_frame = ee_frame

    def buildFromMJCF(self, mjcf_file):
        """从 MJCF 文件构建 Pinocchio 模型，并缓存末端 frame 的 ID。"""
        self.arm = pin.RobotWrapper.BuildFromMJCF(mjcf_file)
        self.model = self.arm.model
        self.data = self.arm.data
        self.ee_id = self.model.getFrameId(self.ee_frame)
        if self.ee_id == self.model.nframes:
            raise ValueError(f"Pinocchio frame not found: {self.ee_frame}")

    def fk(self, q):
        """调用 Pinocchio FK，返回末端 frame 在世界坐标系下的 4x4 齐次变换矩阵。"""
        q_pin = np.zeros(self.model.nq)
        q = np.asarray(q, dtype=np.float64)
        q_pin[: min(q.size, q_pin.size)] = q[: min(q.size, q_pin.size)]
        pin.forwardKinematics(self.model, self.data, q_pin)
        pin.updateFramePlacements(self.model, self.data)
        se3_obj = self.data.oMf[self.ee_id]
        tf = np.eye(4, dtype=np.float64)
        tf[:3, :3] = se3_obj.rotation
        tf[:3, 3] = se3_obj.translation
        return tf

class PinocchioClik:
    """基于 Pinocchio 的 CLIK。"""
    def __init__(
        self,urdf_path,  # Pinocchio 建模用的机械臂 URDF 路径。
        ee_frame_name,  # IK/FK 使用的末端 frame 名称。
        eps=1e-4,  # 6 维位姿误差的收敛阈值。
        max_iterations=120,  # 每次 IK 求解允许的最大迭代次数。
        integration_step=0.1,  # 把关节速度积分成关节位置时的步长。
        damping=1e-6,  # 阻尼最小二乘里的阻尼系数，奇异位形附近更稳定。):
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
        pin.updateFramePlacements(self.model, self.data)
        # oMf 存的是每个 frame 在世界坐标系下的位姿；这里取末端 frame 的那一项。
        placement = self.data.oMf[self.ee_frame_id]
        return pin.SE3(placement.rotation.copy(), placement.translation.copy())

    def solve(self, current_q, target_pose):
        """从当前关节位置出发，迭代求一个能到达 target_pose 的关节目标。
        这一段是 CLIK 主循环：
        1. 用当前 q 做 FK，得到当前末端位姿。
        2. 计算当前末端到目标末端的 6 维误差。
        3. 用 Jacobian 把末端误差换成关节速度。
        4. 积分得到下一轮 q，并裁剪到关节限位内。
        """
        q = self._to_pin_q(current_q)
        lower = self.model.lowerPositionLimit
        upper = self.model.upperPositionLimit
        reason = "max_iterations"

        # 给误差设置占位值，在随后的迭代中会被覆盖。
        err = np.zeros(6, dtype=np.float64)
        position_error = np.inf
        rotation_error = np.inf
        touched_joint_limit = False

        for iteration in range(self.max_iterations + 1):
            """每一轮迭代,都将做以下工作：
                1.更新关节树、刷新各个 frame 的世界位姿缓存。
                2.求解当前位姿,获取从当前位姿到目标位姿的李群和李代数。
            """
            pin.forwardKinematics(self.model, self.data, q)
            pin.updateFramePlacements(self.model, self.data)
            current_pose = self.data.oMf[self.ee_frame_id]
            current_to_target = current_pose.actInv(target_pose) # SE3
            
            err = pin.log(current_to_target).vector # se3
            position_error = norm(target_pose.translation - current_pose.translation)
            rotation_error = norm(err[3:])

            # 已收敛
            if norm(err) < self.eps:
                reason = "converged" 
                return IkResult(
                    q=q,
                    success=True,
                    iterations=iteration,
                    error=err,
                    position_error=position_error,
                    rotation_error=rotation_error,
                    reason=reason,
                )

            # 未收敛
            jacobian = pin.computeFrameJacobian(
                self.model,
                self.data,
                q,
                self.ee_frame_id,
                pin.ReferenceFrame.LOCAL,
            )
            jacobian = -pin.Jlog6(current_to_target.inverse()) @ jacobian
            try:
                joint_velocity = -jacobian.T @ solve(
                    jacobian @ jacobian.T + self.damping * np.eye(6),
                    err,
                )
            except np.linalg.LinAlgError:
                reason = "singular_jacobian"
                break

            next_q = pin.integrate(self.model, q, joint_velocity * self.integration_step)
            clipped_q = np.clip(next_q, lower, upper)
            if not np.allclose(clipped_q, next_q):
                touched_joint_limit = True
            # 用裁剪后的 q 进入下一轮，避免继续从非法关节位置迭代。
            q = clipped_q
            if touched_joint_limit and reason == "max_iterations":
                reason = "max_iterations_or_joint_limit"

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

class Check:
    """主类，持有 ik、fk 的两个对象，并将他们进行比较"""
    def __init__(self, scene_xml_path, ik_solver, fk_model):
        require_file(scene_xml_path, "MuJoCo scene XML")
        self.model = mujoco.MjModel.from_xml_path(str(scene_xml_path))
        self.data = mujoco.MjData(self.model)
        self.fk_model = fk_model
        self.ik_solver = ik_solver
        self.handle = None
        self.frame_count = 0
        self.print_interval = 30
        self.motion_frames = 300 # 设定最多移动300帧
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

    def apply_joint_target(self, q_target):
        """把 IK 输出的 7 维关节目标写入 MuJoCo 控制接口。"""
        if self.model.nu >= ARM_DOF:
            self.data.ctrl[:ARM_DOF] = q_target[:ARM_DOF]
        else:
            # 兜底路径：如果 XML 没有 actuator，就只能直接写 qpos，作为纯运动学演示。
            self.data.qpos[:ARM_DOF] = q_target[:ARM_DOF]

    def mujoco_ee_pose(self):
        """读取 MuJoCo 中末端 body 的世界位姿，用于和目标位姿做误差记录。"""
        body = self.data.body(self.ee_body_id)
        rotation = body.xmat.reshape(3, 3).copy()
        translation = body.xpos.copy()
        return pin.SE3(rotation, translation)

    def print_status(self, target_pose, ik_result):
        """记录目标、实际、误差和 IK 状态，满足误差检查要求。"""
        actual_pose = self.mujoco_ee_pose()

        # target_*：MuJoCo 实际末端位姿与外层目标位姿之间的跟踪误差。
        actual_to_target = actual_pose.actInv(target_pose) # SE3
        target_pose_error = pin.log(actual_to_target).vector
        target_position_error = norm(target_pose.translation - actual_pose.translation)
        target_rotation_error = norm(target_pose_error[3:])

        # fk_*：同一个 qpos 下，MuJoCo 实际末端位姿与 Pinocchio FK 位姿之间的模型对齐误差。
        q = self.data.qpos[:ARM_DOF]
        fk_tf = self.fk_model.fk(q)
        fk_pose = pin.SE3(fk_tf[:3, :3], fk_tf[:3, 3])
        actual_to_fk = actual_pose.actInv(fk_pose)
        fk_pose_error = pin.log(actual_to_fk).vector
        fk_position_error = norm(actual_pose.translation - fk_pose.translation)
        fk_rotation_error = norm(fk_pose_error[3:])

        print(
            "frame="
            f"{self.frame_count:04d} "
            f"target={np.round(target_pose.translation, 4)} "
            f"actual={np.round(actual_pose.translation, 4)} "
            f"target_pos_err={target_position_error:.5f} "
            f"target_rot_err={target_rotation_error:.5f} "
            f"fk_pos_err={fk_position_error:.5e} "
            f"fk_rot_err={fk_rotation_error:.5e} "
            f"ik_pos_err={ik_result.position_error:.5f} "
            f"ik_rot_err={ik_result.rotation_error:.5f} "
            f"ik_iter={ik_result.iterations} "
            f"ik_reason={ik_result.reason} "
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
            ik_result = self.ik_solver.solve(self.data.qpos[:ARM_DOF], target_pose)
            if ik_result.success:
                self.apply_joint_target(ik_result.q)
            else:                
                self.apply_joint_target(self.data.qpos[:ARM_DOF])
                print(
                    "IK failed: "
                    f"reason={ik_result.reason}, "
                    f"ik_pos_err={ik_result.position_error:.5f}, "
                    f"ik_rot_err={ik_result.rotation_error:.5f}"
                )
            if self.frame_count % self.print_interval == 0:
                self.print_status(target_pose, ik_result)


            mujoco.mj_step(self.model, self.data)
            self.handle.sync()
            self.frame_count += 1
            time.sleep(self.model.opt.timestep)



def main():
    fk_model = PinocchioFk(EE_FRAME_NAME)
    fk_model.buildFromMJCF(ARM_XML_PATH)
    ik_solver = PinocchioClik(URDF_PATH, EE_FRAME_NAME)
    viewer = Check(SCENE_XML_PATH, ik_solver, fk_model)
    viewer.run_loop()

if __name__ == "__main__":
    main()
