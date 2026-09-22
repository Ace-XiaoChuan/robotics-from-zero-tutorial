"""对比 Franka Panda 在 MuJoCo、Pinocchio 和 KDL 中的正运动学结果。

这个脚本会打开 MuJoCo viewer，读取当前关节位置，然后打印三种方式算出来的
末端位姿：

1. MuJoCo 仿真状态里的 body 位置。
2. Pinocchio 基于 MJCF 模型计算的 FK。
3. KDL 基于 URDF 模型计算的 FK。

预期结果是三者在数值误差范围内基本一致。
"""

import sys
from pathlib import Path

import numpy as np
import pinocchio as pin

# 机器人 XML/URDF 模型和辅助模块放在单独的 mujoco-learning 项目里。
# 把路径集中放在这里，换机器或换目录时只需要改这一处。
MUJOCO_LEARNING_ROOT = Path("~/litchi_tutorial/mujoco-learning").expanduser()

# 优先导入环境里已经能找到的 mujoco_learning；如果 PYTHONPATH 里没有，
# 再退回到上面指定的本地源码目录。
try:
    from mujoco_learning import kdl_kinematic, mujoco_viewer
except ModuleNotFoundError as exc:
    if exc.name != "mujoco_learning" or not MUJOCO_LEARNING_ROOT.exists():
        raise
    sys.path.insert(0, str(MUJOCO_LEARNING_ROOT))
    from mujoco_learning import kdl_kinematic, mujoco_viewer


class PinocchioFk:
    """只用于 FK 的轻量 Pinocchio 封装。

    mujoco_learning.pinocchio_kinematic.Kinematics 会额外构建 CasADi IK 求解器。
    这个脚本只做 FK 对比，所以用这个小封装避开不需要的 CasADi 依赖。
    """

    def __init__(self, ee_frame):
        """记录要查询的末端 frame 名字。

        Args:
            ee_frame: Pinocchio 模型里的末端 frame 名字，例如 "link7"。
        """
        self.frame_name = ee_frame

    def buildFromMJCF(self, mjcf_file):
        """从 MJCF 文件构建 Pinocchio 模型，并缓存末端 frame 的 ID。

        Args:
            mjcf_file: MuJoCo MJCF/XML 模型文件路径，例如 panda_pos.xml。
        """
        # 从 MuJoCo 使用的同一份 MJCF 文件构建 Pinocchio 运动学模型。
        # RobotWrapper 是 Pinocchio 提供的一个高级包装类。
        # 把机器人模型、计算数据、几何模型等东西打包到一个对象里，方便使用。
        self.arm = pin.RobotWrapper.BuildFromMJCF(mjcf_file)
        self.model = self.arm.model
        self.data = self.arm.data

        # Pinocchio 内部用数字 frame ID。初始化时先把可读的 frame 名字解析成 ID，
        # 后面 fk() 里直接复用这个 ID。
        self.ee_id = self.model.getFrameId(self.frame_name)
        if self.ee_id == self.model.nframes:
            raise ValueError(f"Pinocchio frame not found: {self.frame_name}")

    def fk(self, q):
        """调用 Pinocchio FK，返回末端 frame 相对世界坐标系的 4x4 位姿矩阵。

        Args:
            q: 当前关节广义位置向量。这里通常传入 MuJoCo 的 data.qpos。
        """
        # MuJoCo 的 qpos 和 Pinocchio 的 q 通常前面都是机械臂关节，后面可能还有
        # 夹爪手指等额外关节。这里先拷贝到 Pinocchio 期望的 q 向量长度。
        # 因为传进来的 q 通常是 MuJoCo 的 self.data.qpos,和 Pinocchio 期望的 q 长度不一定完全一致。
        # 说不定有夹爪的 2 个自由度.
        q_pin = np.zeros(self.model.nq)
        q = np.asarray(q, dtype=np.float64)
        q_pin[: min(q.size, q_pin.size)] = q[: min(q.size, q_pin.size)]

        # pin.forwardKinematics(model: pin.Model, data: pin.Data, q: np.ndarray) -> None
        # 根据当前关节位置 q，更新机器人各 joint 的运动学结果，结果写入 data。
        pin.forwardKinematics(self.model, self.data, q_pin)

        # pin.updateFramePlacements(model: pin.Model, data: pin.Data) -> None
        # 在 joint 位姿更新后，刷新所有 frame 的世界位姿 data.oMf。
        pin.updateFramePlacements(self.model, self.data)

        # 把 Pinocchio 的 SE3 对象转成普通的 4x4 齐次变换矩阵。
        # SE3 是机器人学里表示 三维空间刚体位姿 的数学对象。
        # SE3 = 三维位置 + 三维姿态
        # self.data.oMf[] 是 Pinocchio 里存放每个 frame 在世界坐标系下位姿 的数组。
        # 末端 link7 相对于世界坐标系的 SE3 位姿
        se3_obj = self.data.oMf[self.ee_id]
        tf = np.eye(4, dtype=np.float64)
        tf[:3, :3] = se3_obj.rotation
        tf[:3, 3] = se3_obj.translation
        return tf


class CheckFk(mujoco_viewer.CustomViewer):
    """在 viewer 循环里定期打印 FK 对比结果。"""

    def __init__(self, scene_xml_path, arm_xml_path):
        """初始化 MuJoCo viewer，以及 KDL/Pinocchio 两套 FK 模型。

        Args:
            scene_xml_path: MuJoCo 场景 XML 路径，包含机器人和地面等场景元素。
            arm_xml_path: 单独的机器人 MJCF/XML 路径，供 Pinocchio 构建 FK 模型。
        """
        # CustomViewer 负责创建 MuJoCo model/data，并推进仿真。
        super().__init__(str(scene_xml_path), 3, azimuth=-45, elevation=-30)
        self.arm_xml_path = str(arm_xml_path)

        # MuJoCo、Pinocchio 和 KDL 都使用同一个末端 body/frame 名字，
        # 这样打印出来的位姿才是在对比同一个物理连杆。
        self.ee_body_name = "link7"

        # KDL 使用 Panda 机械臂的 URDF 模型。
        self.arm2 = kdl_kinematic.Kinematics(self.ee_body_name)
        urdf_file = str(MUJOCO_LEARNING_ROOT / "model/franka_panda_urdf/robots/panda_arm.urdf")
        self.arm2.buildFromURDF(urdf_file, "link0")

        # Pinocchio 使用和 MuJoCo 一致的 MJCF 模型。
        self.arm1 = PinocchioFk(self.ee_body_name)
        self.arm1.buildFromMJCF(self.arm_xml_path)

        # viewer 每个 timestep 都会调用 runFunc()。降低打印频率，避免终端刷屏，
        # 也避免过多 print 拖慢渲染。
        self.print_interval = 100

    def runBefore(self):
        """viewer 主循环开始前设置仿真 timestep 和初始关节位置。"""
        self.model.opt.timestep = 0.005
        # 设定初始位置
        # model.key_qpos 存的是 MJCF 里 <keyframe> 定义的预设关节位置快照。
        self.initial_pos = self.model.key_qpos[0]  
        print("Initial position: ", self.initial_pos)
        for i in range(self.model.nq):
            self.data.qpos[i] = self.initial_pos[i]
        self.frame_count = 0

    def runFunc(self):
        """viewer 每帧调用；按固定间隔打印 MuJoCo、Pinocchio 和 KDL 的 FK 结果。"""
        # self.data.qpos[:7] = self.initial_pos[:7]
        # CustomViewer 会在 runFunc() 前调用 mujoco.mj_forward()，所以这里读取到的
        # body xpos 已经和当前 qpos 同步。
        if self.frame_count % self.print_interval == 0:
            print(f"Frame {self.frame_count}")
            print("Mujoco body position: ")
            print(self.getBodyPositionByName(self.ee_body_name))

            # 用当前 MuJoCo qpos 分别调用 Pinocchio 和 KDL 的 FK。
            self.fk_tf1 = self.arm1.fk(self.data.qpos)
            self.fk_tf2 = self.arm2.fk(self.data.qpos)
            print("FK method 1 result: ")
            print(self.fk_tf1)
            print("FK method 2 result: ")
            print(self.fk_tf2)
        self.frame_count += 1


if __name__ == '__main__':
    SCENE_XML_PATH = MUJOCO_LEARNING_ROOT / "model/franka_emika_panda/scene_pos.xml"
    ARM_XML_PATH = MUJOCO_LEARNING_ROOT / "modelD/franka_emika_panda/panda_pos.xml"
    robot = CheckFk(SCENE_XML_PATH, ARM_XML_PATH)
    robot.run_loop()