# 规划与操作：原理专题与 MoveIt / MTC

本文行数：52行，预期阅读时长：4分钟

先读运动规划总览，再按疑问查五个原理专题；MoveIt / MTC 沿用下方六章复习入口。详细日志与历史视频留在对应章节。源码统一放在 `packages/`，保持 ROS 包内的构建、头文件、launch 和配置关系。

| 章节 | 本章回答的问题 | 主要职责 |
| --- | --- | --- |
| [运动规划基础：路径、轨迹与执行](01_motion_planning/README.md) | 什么是可行运动？ | 构型空间、约束、采样规划、路径与时间轨迹的区别 |
| [机器人模型与 MoveIt 配置](02_moveit_setup/README.md) | MoveIt 怎样理解机器人？ | URDF / SRDF、规划组、末端、IK、关节限制、控制器配置关系 |
| [运动请求、笛卡尔路径与执行反馈](03_move_group_interface/README.md) | 怎样提出并检查一次运动？ | MoveGroupInterface 请求、笛卡尔路点、规划与执行返回值、状态反馈 |
| [规划场景、碰撞与物体附着](04_planning_scene/README.md) | 怎样表示环境与碰撞关系？ | 碰撞对象、场景更新、自碰撞、允许碰撞、附着与分离 |
| [MTC：多阶段任务规划](05_mtc_stages/README.md) | 怎样连接多个动作？ | Stage、属性、状态传递、候选解连接与失败定位 |
| [抓放任务：抓取条件、完整流程与结果判断](06_pick_place/README.md) | 怎样判断抓放真正完成？ | 抓取位姿、接近与闭合、接触条件、完整流程、失败分类与结果判据 |

## 规划原理专题

先修为[运动学](../kinematics/README.md)；涉及实际执行时连接[控制专题](../control/README.md)。编号 07～11 用于保留已有六章链接，不表示必须先读完工具章节。

| 专题 | 主要问题 | 例子 |
| --- | --- | --- |
| [07 构型空间](07_configuration_space/README.md) | 怎样表示整台机器人、限位与距离？ | 同一末端位置的两种肘部构型；周期角与有限关节 |
| [08 碰撞检测](08_collision_checking/README.md) | 点合法为什么不代表整段合法？ | 滑块越过薄障碍；几何误差余量 |
| [09 采样规划](09_sampling_planning/README.md) | 怎样连接合法点，怎样理解超时？ | 接受绕路边、拒绝穿障碍的捷径 |
| [10 约束规划](10_constrained_planning/README.md) | 怎样让整个过程维持任务条件？ | 保持平面工具朝向；圆形约束上的插值 |
| [11 轨迹优化](11_trajectory_optimization/README.md) | 怎样改善路径，为什么平滑不等于可行？ | 平滑代价降低但进入障碍 |

五篇均有速记、静态例子与结果解释；无需运行软件即可复习。数值核对与未验证范围见[验证记录](verification.md)。

## 阅读顺序与内容边界

按“概念 → 配置 → 单次运动 → 场景 → 多阶段任务 → 综合抓放”阅读。第三章先用简单场景理解接口，第四章再展开场景管理。

- 第一章解释原理，第三章解释请求与返回结果。现有绘图几何分析保留在第一章，第三章链接复用。
- 第二章说明控制器配置如何对应；第三章负责执行请求与反馈，动力学和反馈控制算法见[控制专题](../control/README.md)。
- 第二章说明 SRDF 中的静态碰撞配置；第四章负责运行中的场景与碰撞关系变化。
- 第五章解释 MTC 的任务组织，第六章解释抓取条件与任务结果。场景中的附着不等于物体已在物理上被抓牢。

**正文状态：** 六章工具与任务正文、五个原理专题均已补齐，包含速记、静态例子、源码解释和失败定位。文档完成不表示示例已通过构建、控制执行或物理抓放验收；各章注明了验证边界。

## 源码位置

- [hello_moveit](packages/hello_moveit/)：基础规划、笛卡尔绘图和抓放；原 Lesson 5 绘图文件与这里逐字一致，已合并。
- [mtc_tutorial](packages/mtc_tutorial/)：MTC 入门。
- [mtc_week3_demo](packages/mtc_week3_demo/)：原 Lesson 6 桌面抓放案例。
- [mtc_advanced_demo](packages/mtc_advanced_demo/)：环境、任务构建与应用控制拆分。
- [panda_moveit_config](packages/panda_moveit_config/)：小型机器人规划与控制配置。
- [pick_and_place](packages/pick_and_place/)：原包骨架，仅有构建和包声明，未包含抓放实现。

包声明供按需准备环境时参考；未打包 ROS 2、MoveIt、MTC、机器人完整模型库或构建产物。本次不验证控制执行。

[总目录](../README.md) · [目录迁移对照](../../doc/directory-reorganization.md)
