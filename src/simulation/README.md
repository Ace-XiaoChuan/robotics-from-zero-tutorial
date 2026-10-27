# 模型与仿真：以 MuJoCo 为主线

本文行数：47行，预期阅读时长：4分钟

MuJoCo 根据机器人和环境的模型、当前状态与输入，计算下一时刻的运动。本专题帮助你读懂一份场景、一段仿真程序和它的结果，能够说明需要什么功能、判断输入输出，并在异常时找到检查方向。

**先理解“场景 → 状态 → 输入 → 物理步进 → 观测”的过程，再按需查公式、API 和配置。** 各章直接给出例子与结果，无需安装环境或执行代码才能阅读；源码和验证记录用于查阅与复现。

## 十二章目录

| 章节 | 核心问题 | 例子 |
| --- | --- | --- |
| [01 一次 MuJoCo 仿真怎样发生](01_simulation_overview/README.md) | 模型、状态、输入、步进和窗口各负责什么？ | 给单摆一个输入后，运动在哪里产生 |
| [02 场景中的对象与空间关系](02_scene_objects/README.md) | body、joint、geom、site 与坐标层级是什么？ | 关节角与杆尖世界位置 |
| [03 怎样读懂和组织 MJCF 场景](03_mjcf_scenes/README.md) | 场景入口、default、include 和资源怎样组织？ | 将两关节机械臂放入有地面与相机的场景 |
| [04 从模型描述到运行中的仿真](04_model_data/README.md) | XML、MjModel 与 MjData 怎样对应？ | 一个模型创建两份独立状态 |
| [05 状态、计算与时间步进](05_state_step/README.md) | 数组是什么，forward 与 step 有什么区别？ | 改了角度，末端坐标为什么还没更新 |
| [06 输入怎样通过执行器变成运动](06_actuation/README.md) | ctrl 输入什么，传动和限幅怎样生效？ | 相同的数值作为位置目标或 motor 命令 |
| [07 物理参数怎样影响运动](07_physical_parameters/README.md) | 质量、惯量、重力、阻尼和尺度影响什么？ | 质量翻倍，加速度是否总会减半 |
| [08 碰撞、接触、摩擦与约束](08_contact_constraints/README.md) | 物体怎样被支撑，为什么滑动或穿透？ | 方块落地、滑动与关闭碰撞 |
| [09 怎样观察仿真](09_observation/README.md) | 窗口、相机图像与传感器读数怎样对应？ | 同一状态的三种观察方式 |
| [10 初始化、重置、记录与复现](10_reset_recording/README.md) | 怎样重复实验、保存数据和中途恢复？ | 重跑单摆与机械臂的状态快照 |
| [11 从异常现象定位问题](11_debugging/README.md) | 怎样从错误缩小到模型、输入、计算或显示？ | 目标已收到，机械臂却到不了 |
| [12 综合例子：读懂一段机械臂仿真](12_arm_walkthrough/README.md) | 怎样解释并检查一段完整的仿真程序？ | 两关节机械臂的 3 秒运动与力矩不足对照 |

首次阅读可按 **01 → 02 → 03 → 04 → 05 → 06 → 12** 建立主线。遇到物理行为查 07、08，读取数据查 09、10，定位异常查 11；第十二章会链接需要补充的概念。

## 阅读时使用的模型与约定

- [单摆与自由球](mujoco/models/pendulum.xml)：解释模型编译、状态维度、输入与重置。自由球关闭接触，用于观察自由关节。
- [接触方块](mujoco/models/contact_box.xml)：解释地面支撑、接触力和摩擦，质量为 `0.2 kg`。
- [两关节机械臂场景](mujoco/models/arm_scene.xml)：关节顺序为 `[shoulder, elbow]`，杆长 `0.4 m、0.3 m`，在世界系水平面内运动。模型由仓库自建，不代表具体工业机械臂。

默认采用 m、kg、s、rad、N、N·m；世界系 z 轴朝上。局部坐标、旋转表示、输入单位和记录时刻在使用处进一步说明。几何推导、教学示意和实际仿真结果分别注明。

当前复查环境为 **Python 3.10.12 / MuJoCo 3.13.0 / NumPy 2.2.6**。参考资料链接固定到 3.13.0；原单摆在 3.8.1 下的结果也保留于[验证记录](mujoco/verification.md)。查看其他版本文档时，先核对实际安装版本。

## 查阅与复现

- [术语、数据与常用操作速查](mujoco/quick_reference.md)：中英文词汇、接口用途与按问题查阅。
- [模型、源码与依赖](mujoco/README.md)：自带模型、运行入口和小型结果。
- [数值验证记录](mujoco/verification.md)：配置、结果、判据及显示验证情况。
- [从代码到仿真与真机](mujoco/control_flow_reference.md)：带时间的轨迹、MoveIt、FollowJointTrajectory 与 ros2_control 控制链。

这里解释仿真模型和接口的行为。[运动学](../kinematics/README.md)展开 FK、IK 与 Jacobian，[动力学与控制](../control/README.md)展开动力学方程与反馈控制，[感知与估计](../perception/README.md)展开标定与状态估计；通过链接按需复习。

[学习路线 S3](../../doc/learning-roadmap.md#s3) · [知识索引](../../doc/README.md) · [教程与源码目录](../README.md)
