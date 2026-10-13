# S1：空间数学与数值方法

本文行数：28行，预期阅读时长：2分钟

**先明确数字描述的几何对象、参考系和单位，再理解求解方法怎样把误差变成修正量。十章都可直接阅读例子与结果，不要求运行代码。**

| 章节 | 要回答的问题 |
| --- | --- |
| [01 向量、范数与单位方向](01_vectors/README.md) | 位移、距离与方向分别是什么？ |
| [02 点积：沿一个方向有多少分量](02_dot_product/README.md) | 怎样计算投影，符号代表什么？ |
| [03 矩阵乘法与 `@` 运算符](03_matrix_product/README.md) | 数组形状和连乘顺序怎样对应运算？ |
| [04 叉积：垂直方向、旋转轴与力矩](04_cross_product/README.md) | 怎样判断方向，叉积大小是什么？ |
| [05 旋转表示与约定](05_rotations/README.md) | 旋转矩阵、欧拉角、轴角和四元数怎样表达同一朝向？ |
| [06 坐标系、齐次变换与变换链](06_transforms/README.md) | 点怎样从工具系变到基座系，变换怎样复合与求逆？ |
| [07 位姿误差与局部线性化](07_pose_errors/README.md) | 位置和姿态怎样求差，为什么只能做局部近似？ |
| [08 最小二乘、残差与加权](08_least_squares/README.md) | 数据无法完全拟合时怎样求解，权重改变了什么？ |
| [09 SVD、伪逆与阻尼最小二乘](09_pseudoinverse_damping/README.md) | 解不唯一或某方向难以运动时怎么办？ |
| [10 基本约束优化](10_constrained_optimization/README.md) | 目标、变量、硬约束与不可行结果怎样区分？ |

01～06 建立空间表示基础；07～10 可在遇到 IK、标定、轨迹与控制问题时按需复习，不要求先完成整套优化课程再继续机器人主线。机器人 Jacobian、奇异性和冗余的具体推导归[运动学](../../kinematics/README.md)，本主题解释它们使用的数学工具。

## 参考材料与验证

- [旋转与齐次变换案例](examples/rigid_transforms/README.md)：保留原 Lesson 3 源码。
- [已有位姿误差笔记](../../kinematics/examples/model_alignment/lie_group_lie_algebra_notes.md)与[Jacobian、最小二乘及伪逆笔记](../../kinematics/examples/model_alignment/qpos_jacobian_notes.md)：按需查阅代码对应关系，不复制实现参考。
- [数值核对记录](verification.md)与[检查脚本](check_examples.py)：新增六章的 16 项教学数值检查通过，不代表机器人控制或真机验证。

[学习路线 S1](../../../doc/learning-roadmap.md#s1) · [案例索引](../../README.md)
