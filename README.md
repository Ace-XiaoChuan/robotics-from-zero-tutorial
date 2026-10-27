# Robotics From Zero Tutorial

本文行数：32行，预期阅读时长：2分钟

这是个人机器人工程学习笔记与源码仓库，围绕机械臂的建模、感知、规划、控制与仿真展开，也收录机器学习、数据采集和模仿学习。文档先解释技术的用途和输入输出，再用例子帮助复习；公式推导和实现细节放在后面，按需要查阅。

## 从哪里开始

- [知识索引](doc/README.md)：按问题找到对应笔记。
- [学习路线](doc/learning-roadmap.md)：了解各主题之间的关系。
- [教程与源码目录](src/README.md)：查找案例、程序和配置。

## 主题入口

| 主题 | 内容 |
| --- | --- |
| [工程基础](src/foundations/engineering/README.md) | 路径、Git、数值数据、构建与调试 |
| [空间数学](src/foundations/spatial_math/README.md) | 向量、旋转、坐标变换、位姿误差与数值求解 |
| [ROS 2](src/ros2/README.md) | 节点通信、参数、launch、TF 与时间 |
| [模型与仿真](src/simulation/README.md) | MuJoCo 十二章：场景、状态、执行器、接触、观测与排错 |
| [运动学](src/kinematics/README.md) | 正逆运动学、Jacobian、奇异性与工作空间 |
| [动力学与控制](src/control/README.md) | 力矩、关节耦合、动力学计算、轨迹与反馈控制 |
| [感知与估计](src/perception/README.md) | 相机标定、目标位姿、测量误差、滤波与时间对齐 |
| [规划与操作](src/manipulation/README.md) | 运动规划、MoveIt、MTC 与抓放 |
| [数据采集](src/data_collection/README.md) | 图像、机器人状态与 episode 保存 |
| [机器学习](src/machine_learning/README.md) | 从分类、回归到 VLM、模仿学习与强化学习 |

## 仓库内容

`doc/` 保存导航和写作样板，`src/` 按主题保存教程、源码与小型配置。案例的依赖、模型路径和运行方法写在各自的 README 中；数据集、模型权重和运行环境按需要另行准备。

新增笔记参考[文档样板](doc/lesson-template.md)，本地协作约定在 `AGENTS.md` 中维护。
