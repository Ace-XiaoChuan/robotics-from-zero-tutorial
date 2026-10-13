# 文档索引

本文行数：60行，预期阅读时长：3分钟

按主题和问题查找笔记。概念与例子在各章 README 中，较长推导、源码拆解和运行方法由对应章节链接。

## 主题入口

| 主题 | 阅读入口 | 案例 |
| --- | --- | --- |
| 工程基础 | [六个单元](../src/foundations/engineering/README.md) | 路径、Git、构建与调试 |
| 空间数学 | [十章目录](../src/foundations/spatial_math/README.md) | [刚体变换](../src/foundations/spatial_math/examples/rigid_transforms/README.md) |
| ROS 2 | [五章目录](../src/ros2/README.md) | [通信接口](../src/ros2/examples/communication/README.md)、[组件](../src/ros2/examples/composition/README.md) |
| 模型与仿真 | [七章目录](../src/simulation/README.md) | [MuJoCo](../src/simulation/mujoco/README.md) |
| 运动学 | [八章目录](../src/kinematics/README.md) | [模型对齐](../src/kinematics/examples/model_alignment/README.md) |
| 动力学与控制 | [章节目录](../src/control/README.md) | 单关节、多关节、积分与反馈控制 |
| 感知与估计 | [六章目录](../src/perception/README.md) | [相机与 AprilTag](../src/perception/examples/camera_and_tags/README.md) |
| 规划与操作 | [MoveIt / MTC 与规划原理](../src/manipulation/README.md) | [桌面抓放](../src/manipulation/06_pick_place/README.md) |
| 数据采集 | [采集入口](../src/data_collection/README.md) | 图像、状态与 episode 保存 |
| 机器学习 | [20 章导航](../src/machine_learning/README.md) | 分类、回归、神经网络、VLM 与机器人学习 |

各主题的先修关系见[学习路线](learning-roadmap.md)，代码位置见[源码目录](../src/README.md)。

## 整理样板

| 文档 | 内容 |
| --- | --- |
| [Lesson 文档样板](lesson-template.md) | 可复制的课程入口、专题笔记框架及写作约定。 |
| [Lesson 1 课程入口](../src/ros2/examples/communication/README.md) | 通信图、接口说明、环境与运行方法。 |

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
