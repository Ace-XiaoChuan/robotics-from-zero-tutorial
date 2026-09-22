# MoveIt 与操作规划

本文行数：27行，预期阅读时长：2分钟

按下面六章快速复习，详细日志与历史视频留在对应章节。源码统一放在 `packages/`，保持 ROS 包内的构建、头文件、launch 和配置关系。

| 章节 | 主要内容 |
| --- | --- |
| [规划、轨迹与执行](01_motion_planning/README.md) | 目标位姿、可行路径、带时间的轨迹和实际执行是不同对象 |
| [模型与 MoveIt 配置](02_moveit_setup/README.md) | URDF 描述结构，SRDF 描述规划语义；运动学求解配置、关节限制、MoveIt 控制器映射和 ros2_control 配置共同提供案例运行所需的信息 |
| [MoveGroupInterface 与笛卡尔路径](03_move_group_interface/README.md) | 先指定规划组，再设置目标，检查规划结果，最后请求执行 |
| [碰撞场景与物体关系](04_planning_scene/README.md) | 碰撞物体的尺寸、位姿和参考坐标系一起定义障碍物；抓取时还要区分世界物体与附着物体 |
| [MTC 阶段与任务解](05_mtc_stages/README.md) | 任务用 stage 表达阶段；属性决定规划组与末端等上下文 |
| [抓放案例与源码组织](06_pick_place/README.md) | 抓放过程需要同时管理机器人运动、手爪和场景中的物体关系 |

## 源码位置

- [hello_moveit](packages/hello_moveit/)：基础规划、笛卡尔绘图和抓放；原 Lesson 5 绘图文件与这里逐字一致，已合并。
- [mtc_tutorial](packages/mtc_tutorial/)：MTC 入门。
- [mtc_week3_demo](packages/mtc_week3_demo/)：原 Lesson 6 桌面抓放案例。
- [mtc_advanced_demo](packages/mtc_advanced_demo/)：环境、任务构建与应用控制拆分。
- [panda_moveit_config](packages/panda_moveit_config/)：小型机器人规划与控制配置。
- [pick_and_place](packages/pick_and_place/)：原包骨架，仅有构建和包声明，未包含抓放实现。

包声明供按需准备环境时参考；未打包 ROS 2、MoveIt、MTC、机器人完整模型库或构建产物。本次不验证控制执行。

[总目录](../README.md) · [目录迁移对照](../../doc/directory-reorganization.md)
