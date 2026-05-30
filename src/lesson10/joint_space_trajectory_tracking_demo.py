# 关节空间轨迹跟踪 demo 要求：

# 期望关节轨迹 q_des(t)
#         ↓
# 读取当前关节位置 q(t)
#         ↓
# 计算误差 q_des(t) - q(t)
#         ↓
# 通过 position actuator / torque actuator 控制机械臂运动
#         ↓
# 打印或记录 q_des(t)、q(t)、error
import time
import numpy as np
import sys
from pathlib import Path

project_root = Path("~/litchi_tutorial/mujoco-learning").expanduser()
sys.path.append(str(project_root))

from src import mujoco_viewer


class JointSpaceTrajectoryTracking(mujoco_viewer.CustomViewer):
    def __init__(self, path):
        super().__init__(path, 3, azimuth=-45, elevation=-30)
        self.path = path

        # self.logger = 初始化一个logger容器

    # 在仿真开始前执行一次
    def runBefore(
        self,
    ):  # 函数参数都要带self，这个函数是这个对象自己的行为，所以它们需要拿到“自己”

        self.start_time = (
            time.time()
        )  # 注意这里如果只写start_time那就是局部变量，runFunc 访问不到

        # 当前关节位置
        self.q = self.get_current_position()
        self.q_start = self.get_current_position()
        self.q_goal = np.array([0.0, -0.4, 0.0, -1.8, 0.0, 1.4, 0.7])
        self.duration = 5.0

        # 历史记录
        self.q_log = []

        # 当前帧误差
        self.error = np.array([])

        # 所有帧的 error 记录
        self.q_des_log = []
        self.error_log = []

        # 打印计数器
        self.count = 0
        self.max_count = 50

    # 每一帧执行
    def runFunc(self):
        # 已运行时间
        t = time.time() - self.start_time
        self.q = self.get_current_position()
        self.q_des = self.get_desired_position(t)
        self.error = self.q_des - self.q

        # MuJoCo 里的 actuator（执行器）：
        # actuator 不是“关节本身”，而是“把 ctrl 控制输入转换成力/力矩的装置”。
        #
        # 关系大概是：
        #   self.data.ctrl  -> actuator -> actuator_force -> 作用到 joint/tendon/body/site
        #
        # 常见 actuator 类型：
        # 1. motor
        #    直接力/力矩控制。ctrl 表示控制力/力矩大小。适合自己写 PID / PD：
        #       error = q_des - q
        #       torque = kp * error - kd * qvel
        #       ctrl = torque
        # 2. position
        #    位置伺服控制。
        #    ctrl 表示目标位置 q_des。MuJoCo 内部帮你根据“目标位置 - 当前位置”产生力。
        #    所以 position actuator 里：
        #       ctrl = q_des
        #    不是：
        #       ctrl = error
        # 3. velocity
        #    速度伺服控制。ctrl 表示目标速度 qvel_des。
        #    MuJoCo 内部根据“目标速度 - 当前速度”产生力。
        # 4. intvelocity
        #    积分速度控制。
        #    ctrl 像速度命令，但 actuator 内部会积分成一个位置目标。常用于需要“速度输入 + 位置伺服效果”的情况。
        # 5. damper
        #    主动阻尼器。
        #    根据速度产生阻尼力，常用于抑制运动，不是拿来指定目标位置的。
        # 6. cylinder
        #    气缸/液压缸模型。
        #    更接近真实机械执行机构，有自己的动态响应。
        # 7. muscle
        #    肌肉模型。
        #    主要用于生物力学仿真。
        # 8. adhesion
        #    主动吸附/粘附执行器。
        #    用于吸盘、粘附接触之类的模型。
        # 9. general
        #    最通用的 actuator。
        #    可以通过 gainprm / biasprm / dyntype 等参数配置成类似 motor、
        #    position servo、velocity servo 等不同效果。
        # 当前 Panda 模型里的 actuator1~7 是 general actuator，
        # 但它的 gainprm / biasprm 配置形式等价于“位置伺服 + 阻尼”：
        #   actuator_force ≈ kp * (ctrl - q) - kd * qvel
        # 所以在这个 demo 里：
        #   q_des = 目标关节角
        #   q = 当前关节角
        #   error = q_des - q
        #   self.data.ctrl[:7] = q_des
        # error 主要用来观察/记录；
        # 只有在 motor/torque actuator 思路里，才通常用 error 算 ctrl。

        self.data.ctrl[:7] = self.q_des

        # append
        self.q_log.append(self.q)
        self.q_des_log.append(self.q_des)
        self.error_log.append(self.error)

        # counter 每50帧打印一次，防止终端爆炸
        self.count += 1
        if self.count % self.max_count == 0:
            print(f"step={self.count}, error_norm={np.linalg.norm(self.error):.4f}")

    def get_current_position(self):
        return self.data.qpos[0:7].copy()

    def get_desired_position(self, t):
        # 以插值为例
        alpha = min(t / self.duration, 1.0)
        return (1 - alpha) * self.q_start + alpha * self.q_goal # 匀速


test = JointSpaceTrajectoryTracking(
    "/home/ace/mujoco_models/mujoco_menagerie/franka_emika_panda/scene.xml"
)
test.run_loop()
