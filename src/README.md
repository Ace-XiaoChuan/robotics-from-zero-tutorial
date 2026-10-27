# 教程与源码目录

本文行数：61行，预期阅读时长：3分钟

按主题查找教程和代码。各主题的 README 提供概念入口，案例目录保存程序、配置和运行说明；按编号复习已有案例时，使用[案例编号索引](#case-index)。

| 主题 | 内容 | 案例与实现 |
| --- | --- | --- |
| [工程基础](foundations/engineering/README.md) | 路径、Git、Python 数值、C++ 构建、调试与复现 | 六个单元中的小型程序 |
| [空间数学](foundations/spatial_math/README.md) | 向量、旋转、变换、误差、最小二乘与优化 | [刚体变换](foundations/spatial_math/examples/rigid_transforms/README.md)、数值检查 |
| [ROS 2](ros2/README.md) | 接口、参数、QoS、TF 与记录 | [通信案例](ros2/examples/communication/README.md)、[组件案例](ros2/examples/composition/README.md) |
| [模型与仿真](simulation/README.md) | MuJoCo 十二章：场景、状态、执行器、物理参数、接触、观测与排错 | [模型与脚本](simulation/mujoco/README.md)、[两关节机械臂](simulation/12_arm_walkthrough/README.md)、[状态与控制案例](simulation/mujoco/examples/state_and_control/README.md) |
| [运动学](kinematics/README.md) | FK、DH、模型对齐、Jacobian、IK、奇异性、冗余与工作空间 | [模型对齐案例](kinematics/examples/model_alignment/README.md)、平面机械臂数值检查 |
| [动力学与控制](control/README.md) | 力矩、单关节与多关节动力学、积分、轨迹与控制 | 各章的小型模型、检查脚本和结果 |
| [感知与估计](perception/README.md) | 成像标定、位姿、误差传播、Kalman 与时间对齐 | [相机与 AprilTag](perception/examples/camera_and_tags/README.md)、数值检查 |
| [规划与操作](manipulation/README.md) | 六章 MoveIt / MTC 与五个规划原理专题 | `manipulation/packages/` 中的 ROS 包 |
| [数据采集](data_collection/README.md) | 图像、位姿、状态和 episode 保存 | 复用相机与 AprilTag 采集程序 |
| [机器学习](machine_learning/README.md) | 20 章概念、推导与实现说明 | 01～07 的训练代码、共享教学数值程序、VLM 专题例子 |

<a id="target-layout"></a>
<a id="current-layout"></a>

## 目录组织

```text
src/
├── README.md          # 主题导航与案例编号索引
├── foundations/       # engineering、spatial_math
├── ros2/              # 五章笔记与通信、组件案例
├── simulation/        # MuJoCo 十二章；mujoco/ 保存模型和实现
├── kinematics/        # 八章笔记与模型对齐案例
├── control/           # 动力学、积分与控制
├── perception/        # 六章笔记与相机、AprilTag 案例
├── manipulation/      # 规划专题、MoveIt / MTC、packages/
├── data_collection/   # 数据采集入口
└── machine_learning/  # 20 章笔记、训练代码与数值例子
```

<a id="integration"></a>

教程和源码在主题目录维护。MoveIt / MTC 的 ROS 包位于 `manipulation/packages/`，通信与组件包位于 `ros2/examples/` 的对应案例目录。跨主题引用同一份实现，模型路径、依赖和命令在案例入口说明。

<a id="case-index"></a>

## 案例编号索引

按已有 lesson 编号查找对应主题，教程、源码和运行说明统一从下列入口进入。

| 编号 | 案例入口 |
| --- | --- |
| Lesson 1 | [ROS 2 四节点通信与二维任务模拟](ros2/examples/communication/README.md) |
| Lesson 2 | [ROS 2 组件与进程内通信](ros2/examples/composition/README.md) |
| Lesson 3 | [旋转与齐次变换](foundations/spatial_math/examples/rigid_transforms/README.md) |
| Lesson 4 | [标准 DH 与 Modified DH](kinematics/02_dh_conventions/README.md) |
| Lesson 5 | [MoveGroupInterface 运动请求与执行反馈](manipulation/03_move_group_interface/README.md) |
| Lesson 6 | [机械臂抓放任务](manipulation/06_pick_place/README.md) |
| Lesson 7 | [MuJoCo / MJCF 状态与控制](simulation/mujoco/examples/state_and_control/README.md) |
| Lesson 8 | [相机、AprilTag 与传感器数据](perception/examples/camera_and_tags/README.md) |
| Lesson 9 | [模型对齐与末端控制](kinematics/examples/model_alignment/README.md) |

[知识索引](../doc/README.md) · [学习路线](../doc/learning-roadmap.md) · [首页](../README.md)
