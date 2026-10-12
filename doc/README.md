# 文档索引

本文行数：68行，预期阅读时长：5分钟

这里存放学习路线、阶段总结、整理样板和知识导航。默认阅读例子、结果与解释即可复习；具体运行方法按需查阅。案例入口放在各案例目录的 `README.md` 中，已有案例仍可通过 `src/lesson*/` 查找。

## 学习与目录入口

| 文档 | 用途 |
| --- | --- |
| [学习路线](learning-roadmap.md) | 10 个能力阶段，先修关系、实验验收和选修分支；替代原固定 16 周计划。 |
| [总体目录与案例索引](../src/README.md) | 查看按主题整理的实际目录与源码位置。 |
| [机器人学习目录补全计划](robotics-content-plan.md) | 只列尚未完成的工作，按实际需要补充、按项目需要扩展两个优先级维护。 |
| [机器学习 20 章工作目录](../src/machine_learning/机器学习入门实战清单.md) | 保留原八章、深化基础并扩展到 VLM 与机器人学习；维护各章编写范围、材料状态与建设顺序。 |
| [近期处理顺序](learning-roadmap.md#next) | 从已有材料出发安排下一步，不要求重复已经验收的内容。 |

## 按学习阶段查阅

| 阶段 | 路线 | 已有材料入口 |
| --- | --- | --- |
| 工程基础 | [S0](learning-roadmap.md#s0) | [单元索引](../src/foundations/engineering/README.md)、[01 路径与环境](../src/foundations/engineering/01_shell_paths/README.md)、[02 Git 协作](../src/foundations/engineering/02_git/README.md) |
| 空间数学与数值方法 | [S1](learning-roadmap.md#s1) | [十章复习目录](../src/foundations/spatial_math/README.md)、[数值核对](../src/foundations/spatial_math/verification.md)、[变换程序](../src/foundations/spatial_math/examples/rigid_transforms/lesson3.py) |
| ROS 2 | [S2](learning-roadmap.md#s2) | [五章复习目录](../src/ros2/README.md)、 [接口笔记](../src/ros2/examples/communication/ros2_interfaces_notes.md)、[组合案例](../src/ros2/examples/composition/lesson2_composition) |
| 模型与仿真 | [S3](learning-roadmap.md#s3) | [七章复习目录](../src/simulation/README.md)、[控制流与轨迹时间](../src/simulation/00_control_flow/README.md)、[数值验证](../src/simulation/mujoco/verification.md)、[已有 MJCF 笔记](../src/simulation/mujoco/examples/state_and_control/README.md) |
| 运动学 | [S4](learning-roadmap.md#s4) | [八章复习目录](../src/kinematics/README.md)、[数值核对](../src/kinematics/verification.md)、[历史模型对齐案例](../src/kinematics/examples/model_alignment/README.md) |
| 动力学、轨迹与控制 | [S5](learning-roadmap.md#s5) | [零基础七部分目录与参考材料](../src/control/README.md)（01～06 基础概念至控制与约束已补齐，07 待编写）、[轨迹跟踪](../src/simulation/mujoco/examples/state_and_control/joint_space_trajectory_tracking_demo.py)、[末端控制](../src/kinematics/examples/model_alignment/control_ee_with_pinocchio.py) |
| 感知与估计 | [S6](learning-roadmap.md#s6) | [视觉与传感器笔记](../src/perception/examples/camera_and_tags/cv_trainning/README.md)；状态估计待补 |
| 规划与操作 | [S7](learning-roadmap.md#s7) | [MoveIt 例子](../src/manipulation/packages/hello_moveit/src/draw_line_and_circle.cpp)、[MTC](../src/manipulation/06_pick_place/history.md)；[六章 MoveIt / MTC 与五个规划原理专题](../src/manipulation/README.md) |
| 数据与回放 | [S8](learning-roadmap.md#s8) | [episode 采集](../src/perception/examples/camera_and_tags/cv_trainning/demo/sim_camera_tag_pose_demo.py)；回放验收待补 |
| 机器学习与模仿学习 | [S9](learning-roadmap.md#s9) | [20 章导航与已有材料](../src/machine_learning/README.md)：01～20 正文已深化或补齐，16 VLM 可直接阅读；[教学数值核对](../src/machine_learning/examples/README.md)通过，实际策略训练与机器人闭环评估仍待实现 |

## 整理样板

| 文档 | 内容 |
| --- | --- |
| [Lesson 文档样板](lesson-template.md) | 可复制的课程入口、专题笔记框架及写作约定。 |
| [Lesson 1 课程入口](../src/ros2/examples/communication/README.md) | 已整理的完整示例：目标、通信图、环境、运行步骤和验证状态。 |

## 工程基础知识点速查

| 主题 | 笔记入口 |
| --- | --- |
| cwd、脚本目录、绝对与相对路径 | [工作目录与路径](../src/foundations/engineering/01_shell_paths/notes.md#paths) |
| 内置资源与用户输入路径 | [文件定位约定](../src/foundations/engineering/01_shell_paths/notes.md#file-policy) |
| PATH、解释器与 IDE 环境差异 | [命令查找](../src/foundations/engineering/01_shell_paths/notes.md#commands) |
| 空格路径、引号和变量展开 | [引号与展开](../src/foundations/engineering/01_shell_paths/notes.md#quoting) |
| export、子进程与 source | [环境继承](../src/foundations/engineering/01_shell_paths/notes.md#environment)、[脚本执行范围](../src/foundations/engineering/01_shell_paths/notes.md#source) |
| 错误层次与退出码 | [权限、输出与退出码](../src/foundations/engineering/01_shell_paths/notes.md#errors) |
| Git 差异、提交与推送 | [单元 02](../src/foundations/engineering/02_git/README.md)、[差异速查](../src/foundations/engineering/02_git/notes.md#diff) |
| 版本恢复与文件管理 | [Git 协作速查](../src/foundations/engineering/02_git/notes.md#checkpoint) |

## ROS 2 知识点速查

先读 [ROS 2 五章教程](../src/ros2/README.md)，每章约 4 分钟；需要完整源码拆解时，再查看 [Lesson 1 详细笔记](../src/ros2/examples/communication/ros2_interfaces_notes.md)。

| 主题 | 笔记入口 |
| --- | --- |
| Topic / Service / Action 如何选择 | [01 节点与接口](../src/ros2/01_nodes_interfaces/README.md) |
| 名称、命名空间、参数与启动 | [02 参数与 launch](../src/ros2/02_parameters_launch/README.md) |
| 发布订阅、消息字段、QoS 和时间戳 | [Topic](../src/ros2/examples/communication/ros2_interfaces_notes.md#topics) |
| 异步请求、Future 与缓存状态 | [Service](../src/ros2/examples/communication/ros2_interfaces_notes.md#services) |
| 目标接受、反馈、结果与取消 | [Action](../src/ros2/examples/communication/ros2_interfaces_notes.md#actions) |
| 自定义 srv/action 与接口生成 | [自定义接口](../src/ros2/examples/communication/ros2_interfaces_notes.md#interfaces) |
| QoS、Executor、回调组与组件 | [03 QoS 与执行](../src/ros2/03_qos_executors/README.md) |
| TF 方向、坐标链、时间戳与仿真时钟 | [04 TF 与时间](../src/ros2/04_tf_time/README.md) |
| rosbag2、数据新鲜度与分层排错 | [05 记录与排错](../src/ros2/05_recording_debugging/README.md) |
| ROS 2 构建与 launch | [构建与启动](../src/ros2/examples/communication/ros2_interfaces_notes.md#build) |
| 通信排错与场景示例 | [问题记录](../src/ros2/examples/communication/ros2_interfaces_notes.md#issues)、[例子与解释](../src/ros2/examples/communication/ros2_interfaces_notes.md#experiments) |
