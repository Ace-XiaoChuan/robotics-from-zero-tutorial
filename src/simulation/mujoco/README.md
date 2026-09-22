# MuJoCo：模型、状态与可编程仿真

本文行数：25行，预期阅读时长：2分钟

**先理解状态与输入的含义，再用步进推进物理；看到机器人移动不等于完成了控制验证。**

先读[控制流导读：从代码到仿真与真机](../00_control_flow/README.md)，理解带时间的关节轨迹和执行接口，再读[通用模型概念](../01_robot_models/README.md)，随后按下表复习。

| 章节 | 核心例子 |
| --- | --- |
| [01 模型加载](01_model_loading/README.md) | 自带模型与外部 Panda 资源的边界 |
| [02 状态与步进](02_state_step/README.md) | hinge + free joint，nq=8 而 nv=7 |
| [03 控制输入](03_control_inputs/README.md) | ctrl=3 时，限幅后的 motor 力矩为 2 N·m |
| [04 显示与频率](04_viewer_rendering/README.md) | 500 Hz 物理、100 Hz 控制、25 Hz 画面 |
| [05 重置与记录](05_reset_recording/README.md) | 两次相同初态与输入的 100 步记录比较 |

## 实现参考

- [自带模型](models/pendulum.xml)、[检查脚本](check_basics.py)、[固定依赖](requirements.txt)与[实际验证记录](verification.md)。
- 小模型为本仓库教学编写，无外部 mesh、私有模块或私人模型路径；本次使用已安装解释器运行，独立环境安装尚未验证。
- [本地工作区与旧材料](materials.md)、[Lesson 7 原笔记](examples/state_and_control/README.md)、[相机资料](../../perception/examples/camera_and_tags/cv_trainning/README.md)与 [FK 代码](../../kinematics/examples/model_alignment/check_fk_with_mujoco.py)保留原位置。

[返回仿真目录](../README.md) · [总体目录](../../README.md)

[历史状态与控制案例](examples/state_and_control/README.md)。
