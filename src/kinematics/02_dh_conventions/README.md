# 02：标准 DH 与 Modified DH

本文行数：79行，预期阅读时长：4分钟

**DH 是给串联机构建立坐标系、用四个参数描述相邻变换的约定。标准 DH 与 Modified DH 的建系和乘法顺序不同，不能直接共用一张参数表。**

## 速记要点

- 采用右手系、列向量；a、d 是长度，本文新例统一用 m；alpha、theta 是角度，统一用 rad。
- 标准 DH 的第 i 个关节轴沿 `z_(i-1)`；本章 Craig Modified DH 的第 i 个关节轴沿 `z_i`。
- 转动关节通常让 theta 随 q 变化，移动关节通常让 d 随 q 变化；零位偏置应明确记录。
- 公垂线用于确定相邻关节轴之间的 x 方向；轴相交或平行时有建系选择，参数表不是脱离坐标图的唯一答案。

## 四个参数怎样读

| 参数 | 标准 DH 中的含义 | Craig Modified DH 中的含义 |
| --- | --- | --- |
| a | `a_i`，沿 x_i 连接 z_(i-1) 与 z_i 的有符号距离 | `a_(i-1)`，沿 x_(i-1) 连接 z_(i-1) 与 z_i 的有符号距离 |
| alpha | `alpha_i`，绕 x_i 从 z_(i-1) 转到 z_i 的角度 | `alpha_(i-1)`，绕 x_(i-1) 从 z_(i-1) 转到 z_i 的角度 |
| d | `d_i`，沿 z_(i-1) 的偏距 | `d_i`，沿 z_i 的偏距 |
| theta | `theta_i`，绕 z_(i-1) 的角度 | `theta_i`，绕 z_i 的角度 |

参数下标依赖这里的明确约定。不能只看文件写着“DH”，就假设采用同一建系方法。

## 变换顺序决定了矩阵

相邻坐标变换 `T_(i-1)_i` 的两种常见写法为：

$$
T^{\mathrm{standard}}_{i-1,i}
=R_z(\theta_i)T_z(d_i)T_x(a_i)R_x(\alpha_i)
$$

$$
T^{\mathrm{Craig}}_{i-1,i}
=R_x(\alpha_{i-1})T_x(a_{i-1})R_z(\theta_i)T_z(d_i)
$$

同一 x 轴的 Rx 和 Tx 可交换顺序；这不意味着其他因子也能任意交换。[原 Lesson 4 源码](lesson4_Modified_D-H.py)中的 `get_dh_matrix(a, alpha, d, theta)` 对应第二种，矩阵为：

$$
\begin{bmatrix}
c_\theta&-s_\theta&0&a\\
s_\theta c_\alpha&c_\theta c_\alpha&-s_\alpha&-d s_\alpha\\
s_\theta s_\alpha&c_\theta s_\alpha&c_\alpha&d c_\alpha\\
0&0&0&1
\end{bmatrix}
$$

其中 c、s 分别表示 cos、sin。注意第一行的平移为 a，而不是标准 DH 中的 `a*cos(theta)`。

## 例子：同一平面 2R，使用两套正确的参数

沿用 `L1=0.4 m`、`L2=0.3 m`，关节顺序 `[q1,q2]`。所有 alpha、d 都为零。

| 约定 | 第一段 | 第二段 | 固定工具段 |
| --- | --- | --- | --- |
| 标准 DH | `a1=0.4, theta1=q1` | `a2=0.3, theta2=q2` | 无额外偏移 |
| Craig Modified DH | `a0=0, theta1=q1` | `a1=0.4, theta2=q2` | `Tx(0.3)` |

标准 DH 链为 `Rz(q1) @ Tx(0.4) @ Rz(q2) @ Tx(0.3)`；Modified DH 链在这个平面例子中也化为同一个表达式。工具段是固定长度，不是第三个可动关节。

**结果：** `q=[0,pi/2]` 时，两套正确建模都得到位置 `[0.4,0.3,0] m`、绕 z 的 90° 朝向，与几何 FK 一致。

若把标准 DH 的两行 a 值直接传给 Modified DH 函数、且不增加工具段，则会得到 `[0.7,0,0] m`。这不是浮点误差，而是描述了另一条变换链。

## 原脚本怎样复习

原脚本使用长度数值 `10` 和 `5`、角度 30° 和 45°，未明确声明长度单位。其输出位置为约 `[9.954349,9.829629]`，单位与输入长度相同，不能直接标为 m。

本次保留源码，执行其 NumPy 数值部分，将结果与几何公式比较；另以非零 alpha、d 核对 `get_dh_matrix` 与 Craig 因子连乘一致。验证范围见[记录](../verification.md)，不涉及机器人模型或仿真。

## 易错点

- theta 通常是模型角，不一定直接等于编码器读数，可能包含方向和零位偏置。
- URDF 的 origin 与 axis 不是现成的 DH 四参数表；应通过坐标关系转换，而不是按文件字段逐项抄写。
- 检查多组非零关节角；全零或某些特殊姿态可能掩盖连乘、轴方向和工具偏移错误。

[上一章：正运动学](../01_forward_kinematics/README.md) · [返回目录](../README.md) · [下一章：模型对齐](../03_model_alignment/README.md)
