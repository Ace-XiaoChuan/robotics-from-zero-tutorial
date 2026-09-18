# 文档索引

本文行数：64行，预期阅读时长：4分钟

这里存放学习路线、阶段总结、整理样板和知识导航。默认阅读例子、结果与解释即可复习；具体运行方法按需查阅。案例入口放在各案例目录的 `README.md` 中，已有案例仍可通过 `src/lesson*/` 查找。

## 学习与目录入口

| 文档 | 用途 |
| --- | --- |
| [学习路线](learning-roadmap.md) | 10 个能力阶段，先修关系、实验验收和选修分支；替代原固定 16 周计划。 |
| [总体目录与案例索引](../src/README.md) | 查看机器人、MuJoCo、MoveIt 与机器学习的总体章节架构，区分目标目录和已有材料。 |
| [近期处理顺序](learning-roadmap.md#next) | 从已有材料出发安排下一步，不要求重复已经验收的内容。 |

## 按学习阶段查阅

| 阶段 | 路线 | 已有材料入口 |
| --- | --- | --- |
| 工程基础 | [S0](learning-roadmap.md#s0) | [单元索引](../src/foundations/engineering/README.md)、[01 路径与环境](../src/foundations/engineering/01_shell_paths/README.md)、[02 Git 协作](../src/foundations/engineering/02_git/README.md) |
| 空间数学 | [S1](learning-roadmap.md#s1) | [向量与矩阵](../src/foundations/spatial_math/README.md)、[变换程序](../src/lesson3/lesson3.py) |
| ROS 2 | [S2](learning-roadmap.md#s2) | [接口笔记](../src/lesson1/ros2_interfaces_notes.md)、[组合案例](../src/lesson2/lesson2_composition/) |
| 模型与仿真 | [S3](learning-roadmap.md#s3) | [MuJoCo 目录与材料](../src/simulation/mujoco/README.md)、[已有 MJCF 笔记](../src/lesson7/README.md) |
| 运动学 | [S4](learning-roadmap.md#s4) | [MDH 例子](../src/lesson4/lesson4_Modified_D-H.py)、[Jacobian](../src/lesson9/qpos_jacobian_notes.md)、[位姿误差](../src/lesson9/lie_group_lie_algebra_notes.md) |
| 动力学与控制 | [S5](learning-roadmap.md#s5) | [轨迹跟踪](../src/lesson7/joint_space_trajectory_tracking_demo.py)、[末端控制](../src/lesson9/control_ee_with_pinocchio.py) |
| 感知与估计 | [S6](learning-roadmap.md#s6) | [视觉与传感器笔记](../src/lesson8/cv_trainning/README.md)；状态估计待补 |
| 规划与操作 | [S7](learning-roadmap.md#s7) | [MoveIt 例子](../src/lesson5/draw_line_and_circle.cpp)、[MTC](../src/lesson6/README.md)；完整 MoveIt 工作区：`~/moveit-from-zero-tutorial` |
| 数据与回放 | [S8](learning-roadmap.md#s8) | [episode 采集](../src/lesson8/cv_trainning/demo/sim_camera_tag_pose_demo.py)；回放验收待补 |
| 机器学习与模仿学习 | [S9](learning-roadmap.md#s9) | `~/machine_learning_project`：KNN、决策树、聚类、PyTorch 与迁移学习；机器人策略闭环评估待建设 |

## 整理样板

| 文档 | 内容 |
| --- | --- |
| [Lesson 文档样板](lesson-template.md) | 可复制的课程入口、专题笔记框架及写作约定。 |
| [Lesson 1 课程入口](../src/lesson1/README.md) | 已整理的完整示例：目标、通信图、环境、运行步骤和验证状态。 |

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

以下为已经细化到章节的 Lesson 1 入口，其他主题随逐课整理继续扩充。

| 主题 | 笔记入口 |
| --- | --- |
| Topic / Service / Action 如何选择 | [通信方式与接口类型](../src/lesson1/ros2_interfaces_notes.md#concepts) |
| 节点名、可执行文件名与接口名称 | [名称与对象](../src/lesson1/ros2_interfaces_notes.md#names) |
| 发布订阅、消息字段、QoS 和时间戳 | [Topic](../src/lesson1/ros2_interfaces_notes.md#topics) |
| 异步请求、Future 与缓存状态 | [Service](../src/lesson1/ros2_interfaces_notes.md#services) |
| 目标接受、反馈、结果与取消 | [Action](../src/lesson1/ros2_interfaces_notes.md#actions) |
| 自定义 srv/action 与接口生成 | [自定义接口](../src/lesson1/ros2_interfaces_notes.md#interfaces) |
| spin、Executor、线程与共享状态 | [执行机制](../src/lesson1/ros2_interfaces_notes.md#execution) |
| ROS 2 构建与 launch | [构建与启动](../src/lesson1/ros2_interfaces_notes.md#build) |
| 通信排错与场景示例 | [问题记录](../src/lesson1/ros2_interfaces_notes.md#issues)、[例子与解释](../src/lesson1/ros2_interfaces_notes.md#experiments) |
