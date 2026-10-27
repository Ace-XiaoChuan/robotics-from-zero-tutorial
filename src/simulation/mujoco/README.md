# MuJoCo 模型、程序与验证入口

本文行数：25行，预期阅读时长：2分钟

**十二章教程统一从[模型与仿真目录](../README.md)阅读；本目录保存模型、源码、速查和数值验证记录。**

| 材料 | 用途 |
| --- | --- |
| [models/pendulum.xml](models/pendulum.xml) | 单摆与自由关节小模型，解释维度、输入和重置 |
| [models/arm_scene.xml](models/arm_scene.xml) · [planar_arm.xml](models/planar_arm.xml) | 两关节机械臂与场景，解释 include、默认类、伺服和观测 |
| [models/contact_box.xml](models/contact_box.xml) | 自由方块与地面，解释支撑、摩擦和过滤 |
| [check_basics.py](check_basics.py) | 无窗口检查模型编译、状态、输入和重复性 |
| [arm_walkthrough.py](arm_walkthrough.py) | 3 秒机械臂运动；默认无窗口，可选 --viewer 或 CSV 输出 |
| [check_tutorial.py](check_tutorial.py) · [结果](results/tutorial_metrics.json) | 8 组数值检查及正常、异常对照 |
| [requirements.txt](requirements.txt) · [验证记录](verification.md) | 当前固定依赖、命令与验证情况 |
| [quick_reference.md](quick_reference.md) | 中英文术语、字段和操作速查 |
| [control_flow_reference.md](control_flow_reference.md) | MoveIt、ROS 控制链与带时间的轨迹 |
| [状态与控制源码及原 Lesson 7 笔记](examples/state_and_control/README.md) | 较完整的 API、PID 和轨迹跟踪参考 |
| [Panda 外加关节力脚本](materials.md) | PID 控制量、外加力入口与模型配置 |

相关主题：[相机资料](../../perception/examples/camera_and_tags/cv_trainning/README.md) · [FK 代码](../../kinematics/examples/model_alignment/check_fk_with_mujoco.py)。

当前教程在 MuJoCo 3.13.0 / NumPy 2.2.6 下核对。历史控制章节的 MuJoCo 3.8.1 环境另见 [requirements-3.8.1.txt](requirements-3.8.1.txt)，用于匹配原始实验记录。

[返回模型与仿真](../README.md) · [总体目录](../../README.md)
