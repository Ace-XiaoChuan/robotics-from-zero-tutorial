# 模型与仿真

本文行数：21行，预期阅读时长：2分钟

**S3 先看代码怎样驱动仿真与真机，再看模型如何定义机器人、状态如何随仿真步进变化。下面各章可直接阅读，不要求运行代码。**

| 顺序 | 章节 | 要回答的问题 |
| --- | --- | --- |
| 1 | [控制流导读：从代码到仿真与真机](00_control_flow/README.md) | 带时间的轨迹是什么，MoveIt 指令怎样到达执行器？ |
| 2 | [机器人模型](01_robot_models/README.md) | 刚体、关节、惯性、碰撞与工具位置分别是什么？ |
| 3 | [模型加载](mujoco/01_model_loading/README.md) | XML 怎样变成 model 与 data？ |
| 4 | [状态与步进](mujoco/02_state_step/README.md) | nq / nv 为什么不同，forward 与 step 有什么区别？ |
| 5 | [控制输入](mujoco/03_control_inputs/README.md) | ctrl 是力矩还是目标位置？ |
| 6 | [显示与频率](mujoco/04_viewer_rendering/README.md) | 物理、控制与画面为什么不用同一频率？ |
| 7 | [重置与记录](mujoco/05_reset_recording/README.md) | 怎样从相同条件重跑，并正确记录状态？ |

七章采用“速记 + 例子 + 结果与解释”：导读建立控制流与轨迹时间的整体印象，后续以仓库自带单摆和自由关节说明仿真核心概念。原有 [Lesson 7](mujoco/examples/state_and_control/README.md) 保留作详细参考；PID 和轨迹跟踪的深入分析属于 S5。

[数值验证与环境边界](mujoco/verification.md) · [旧 MuJoCo 材料清点](mujoco/materials.md)

[学习路线 S3](../../doc/learning-roadmap.md#s3) · [总体目录](../README.md)
