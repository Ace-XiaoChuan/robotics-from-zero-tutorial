# S4：运动学与数值求解

本文行数：27行，预期阅读时长：2分钟

**先明确机器人模型与任务，再从关节构型求位姿、从目标求关节解，并理解哪些方向能动、哪些限制会让任务失败。八章按“速记 + 例子 + 结果与解释”组织，无需执行代码即可复习。**

| 章节 | 要回答的问题 |
| --- | --- |
| [01 构型、关节空间与正运动学](01_forward_kinematics/README.md) | 给定关节角，末端在哪里、朝向哪里？ |
| [02 标准 DH 与 Modified DH](02_dh_conventions/README.md) | 坐标系与参数表怎样决定变换链，为什么不能混用约定？ |
| [03 关节映射、基座与工具对齐](03_model_alignment/README.md) | 两个库的 FK 为什么可能不同，怎样确认比较的是同一状态和工具点？ |
| [04 Jacobian 与微分运动学](04_jacobian/README.md) | 关节的小变化与速度怎样影响任务量？ |
| [05 解析逆运动学与数值迭代](05_inverse_kinematics/README.md) | 多解、不可达和没有收敛分别是什么意思？ |
| [06 奇异性、秩与可操作性](06_singularities/README.md) | 为什么某个方向突然难以运动，奇异性与限位有什么区别？ |
| [07 冗余、零空间与次要目标](07_redundancy/README.md) | 多出来的关节自由度怎样利用，末端不动具体保持了什么？ |
| [08 工作空间、关节限制与可达性](08_workspace_limits/README.md) | 长度够得着、IK 有解、路径可行和能够执行有什么区别？ |

多数例子采用固定基座的平面 2R，长度 `0.4 m`、`0.3 m`，关节顺序 `[q1,q2]`、角度单位 rad。冗余章改用 3R，并单独声明模型。示例数值不代表 Panda 或其他实际机械臂参数。

## 数学前置与已有案例

- [空间数学与数值方法](../foundations/spatial_math/README.md)：复用旋转、变换、位姿误差、最小二乘与阻尼解释，本主题侧重机器人中的几何含义。
- [Modified DH 历史源码](02_dh_conventions/lesson4_Modified_D-H.py)：保留原 Lesson 4，本次数值结果已核对。
- [模型对齐与末端控制历史案例](examples/model_alignment/README.md)：保留原 Lesson 9 的代码、辅助模块与专题笔记；完整外部模型和控制运行未验证。
- [数值核对记录](verification.md)与[检查脚本](check_examples.py)：26 项检查通过，包含 FK、Jacobian、IK 及失败行为、奇异性和冗余；不代表动力学或真机验证。

[学习路线 S4](../../doc/learning-roadmap.md#s4) · [总目录](../README.md) · [后续：动力学、轨迹与控制](../control/README.md)
