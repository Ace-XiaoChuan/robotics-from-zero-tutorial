import mujoco
import mujoco.viewer
import numpy as np
import time

# 1. 加载模型和数据
xml_path = "mujoco_menagerie/franka_emika_panda/scene.xml"
model = mujoco.MjModel.from_xml_path(xml_path)
data = mujoco.MjData(model)

# 2. 定义目标姿态 (7个关节的关节空间表示)
# 注意：它既不是 $1 \times 7$ 也不是 $7 \times 1$ 的矩阵。在 NumPy 中，像这样直接用一个列表创建出来的结构是一个一维数组
q_target = np.array([0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785])

# 3. 设置 PID 控制器参数
# Kp (Proportional 比例，刚度): 负责快速靠近目标
Kp = np.array([600, 600, 600, 600, 250, 150, 50])
# Kd (Derivative 微分，阻尼): 负责抑制震荡，提供平滑度
Kd = np.array([50, 50, 50, 20, 20, 20, 10])
# Ki (Integral 积分): 负责消除微小的稳态误差。通常不需要很大，否则容易引起低频震荡
Ki = np.array([15, 15, 15, 15, 5, 5, 2])

# 明确定义我们要控制的臂部关节数量
num_arm_joints = 7

# 4. 初始化积分器和限幅阈值
integral_e = np.zeros(
    num_arm_joints
)  
# integral_e 当机械臂快要到达目标位置时（比如只差 0.5 度），误差 error_q 已经非常小了。此时 P 项产生的力矩也会非常小。
# 这个时候会发生一个尴尬的情况：这最后一点点微弱的力矩，可能根本克服不了机械臂关节内部的摩擦力，或者重力的残余影响。
# 于是，机械臂就停在了离目标还差 0.5 度的地方，再也过不去了。这在控制理论中被称为稳态误差 (Steady-State Error)。
# 因此需要引入积分限幅 (Anti-Windup): 防止积分项积累过大导致动作突变或超调
# 这里的数值代表积分项能输出的最大力矩贡献，你可以根据实际表现微调
max_integral_torque = np.array([20, 20, 20, 20, 10, 5, 2])

# 获取仿真的步长 (dt)，用于计算积分
dt = model.opt.timestep

# 5. 启动 Viewer
with mujoco.viewer.launch_passive(model, data) as viewer:

    # 仿真主循环
    while viewer.is_running():
        step_start = time.time()

        # --- PID 控制逻辑开始 ---

        # a. 获取状态

        # q 可能取自法语单词 quantité，即“数量”或“变量”。是分析力学留给机器人学的遗产。
        # q 为广义坐标/关节位置；q-dot 为相对关节速度(即下文 qdot_current)(与之对应的是广义速度即笛卡尔速度，二者通过雅可比矩阵相变换);q-double-dot 为关节加速度（角加速度）。
        # 笛卡尔空间（更严谨的统称是欧几里得空间 Euclidean Space）的核心特征不是维度，而是**“绝对平坦” (Flat)** 和 “刚性”。
        # “三维可弯曲的”是黎曼空间
        q_current = data.qpos[
            :num_arm_joints
        ]  
        qdot_current = data.qvel[:num_arm_joints]

        # b. 计算位置误差和速度误差
        # PID 控制计算误差的通用逻辑永远是：误差 = 目标期望值 - 当前实际值。
        error_q = q_target - q_current
        error_qdot = 0.0 - qdot_current

        # c. 累加误差计算积分项
        integral_e += error_q * dt

        # d. 核心技巧：积分限幅 (Anti-Windup)
        # 限制 Ki * integral_e 的输出范围在 [-max_integral_torque, max_integral_torque] 之间
        integral_term = Ki * integral_e
        integral_term = np.clip(
            integral_term, -max_integral_torque, max_integral_torque
        )

        # e. 计算最终的 PID 力矩
        # tau = Kp*e + Kd*edot + Ki*∫e dt
        tau = Kp * error_q + Kd * error_qdot + integral_term

        # f. 重力补偿
        tau += data.qfrc_bias[:num_arm_joints]

        # g. 施加力矩
        data.qfrc_applied[:num_arm_joints] = tau

        # --- PID 控制逻辑结束 ---

        # 步进仿真
        mujoco.mj_step(model, data)

        # 同步 Viewer 更新
        viewer.sync()

        # 保持实时率
        time_until_next_step = dt - (time.time() - step_start)
        if time_until_next_step > 0:
            time.sleep(time_until_next_step)
