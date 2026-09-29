# MuJoCo 实现参考

本文行数：19行，预期阅读时长：1分钟

**七章教程统一从[模型与仿真目录](../README.md)阅读；本目录保存模型、源码、依赖和验证记录。**

| 材料 | 用途 |
| --- | --- |
| [models/pendulum.xml](models/pendulum.xml) | 七章共用的单摆与自由关节小模型，无外部 mesh |
| [check_basics.py](check_basics.py) | 无窗口检查模型编译、状态、输入和重复性 |
| [requirements.txt](requirements.txt) · [验证记录](verification.md) | 固定依赖、运行命令、历史结果与未验证边界 |
| [状态与控制源码及原 Lesson 7 笔记](examples/state_and_control/README.md) | 较完整的 API、PID 和轨迹跟踪参考 |
| [旧材料清点](materials.md) | 旧脚本、外部模型和迁入材料的来源与限制 |

模型与脚本保留原位置，已有运行命令不变。独立环境安装、外部 Panda 与 Viewer 的验证边界以验证记录为准。

相关主题：[相机资料](../../perception/examples/camera_and_tags/cv_trainning/README.md) · [FK 代码](../../kinematics/examples/model_alignment/check_fk_with_mujoco.py)。

[返回模型与仿真](../README.md) · [总体目录](../../README.md)
