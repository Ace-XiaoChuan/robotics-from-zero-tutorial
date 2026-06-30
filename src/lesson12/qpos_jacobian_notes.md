# Lesson 12 笔记：qpos、最小二乘、雅可比矩阵和伪逆

这份笔记用于帮助以后重新理解 Lesson 12 里 FK/IK 相关代码。重点不是推公式，而是把这些概念和机器人代码里的变量对应起来。

## 1. qpos 是什么

`qpos` 是 MuJoCo 里的 generalized position，也就是**广义位置**。

它不是单纯的三维位置 `[x, y, z]`。对不同类型的关节，`qpos` 的含义不同：

- `revolute` 旋转关节：`qpos[i]` 是角度，单位是 rad。
- `slide` / `prismatic` 平移关节：`qpos[i]` 是位移，单位是 m。
- `free joint`：`qpos` 会包含位置和四元数姿态。

以 Panda 机械臂为例，`qpos` 可能类似：

```python
qpos = [
    0.0,     # qpos[0]: joint1 角度，rad
    -0.4,    # qpos[1]: joint2 角度，rad
    0.0,     # qpos[2]: joint3 角度，rad
    -2.2,    # qpos[3]: joint4 角度，rad
    0.0,     # qpos[4]: joint5 角度，rad
    2.0,     # qpos[5]: joint6 角度，rad
    0.8,     # qpos[6]: joint7 角度，rad
    0.04,    # qpos[7]: left finger slide joint，m
    0.04,    # qpos[8]: right finger slide joint，m
]
```

所以 `qpos[3] = -2.2` 通常表示第 4 个机械臂关节 `joint4` 绕自己的关节轴转了 `-2.2 rad`。

## 2. qpos 不规定连杆长度

连杆长度、关节相对位置、关节轴方向都在模型文件里定义：

- URDF 里通常是 `<origin xyz="..." rpy="...">` 和 `<axis xyz="...">`。
- MJCF 里通常是 `<body pos="..." quat="...">` 和 `<joint axis="...">`。

可以这样记：

```text
URDF / MJCF：规定机器人骨架
qpos：规定每个自由度当前取值
FK：用骨架 + qpos 算末端位姿
```

所以 `qpos` 这个名字里的 `pos` 容易误导。对旋转关节来说，它表示的是广义位置，也就是角度；末端真实空间位置是 FK 间接算出来的。

## 3. FK 和 tf 矩阵

FK 是 forward kinematics，正运动学。

它解决的问题是：

```text
已知关节位置 q，求末端位姿 T
```

数学上可以写成：

```text
T = FK(q)
```

代码里常把位姿矩阵叫 `tf`、`T`、`transform` 或 `T_world_ee`。它通常是一个 `4x4` 齐次变换矩阵：

```text
T = [ R  p ]
    [ 0  1 ]
```

展开是：

```text
[ r11 r12 r13  x ]
[ r21 r22 r23  y ]
[ r31 r32 r33  z ]
[  0   0   0   1 ]
```

其中：

- 左上角 `3x3` 的 `R` 是姿态，rotation matrix。
- 右上角 `3x1` 的 `p` 是位置，position。
- 最后一行固定是 `[0, 0, 0, 1]`。

Lesson 12 里，Pinocchio 和 KDL 返回的 FK 矩阵一致，说明两边模型的运动链、关节轴和输入的 `qpos` 基本一致。

## 4. 雅可比矩阵是什么

雅可比矩阵 Jacobian 连接的是：

```text
关节速度 -> 末端速度
```

写成公式：

```text
v = J(q) * qdot
```

其中：

- `q` 是当前关节位置。
- `qdot` 是关节速度。
- `v` 是末端速度。
- `J(q)` 是当前姿态下的雅可比矩阵。

对一个 `n` 自由度机械臂，常见的空间雅可比维度是：

```text
J: 6 x n
qdot: n x 1
v: 6 x 1
```

`v` 的 6 维通常包含：

```text
[vx, vy, vz, wx, wy, wz]
```

也就是：

- 前 3 维：末端线速度。
- 后 3 维：末端角速度。

注意：不同库可能使用不同顺序或不同参考坐标系，比如 world frame、local frame、local-world-aligned frame。写机器人代码时要确认库的约定。

## 5. 雅可比和 FK 的关系

FK 给的是：

```text
q -> T
```

雅可比给的是局部线性近似：

```text
小的关节变化 dq -> 小的末端变化 dx
```

写成：

```text
dx ≈ J(q) * dq
```

这句话很重要。它表示：在当前 `q` 附近，如果关节稍微动一点 `dq`，末端大概会动 `dx`。

IK 反解会利用这个关系：

```text
我想让末端动 dx，需要关节动多少 dq？
```

也就是尝试解：

```text
J(q) * dq ≈ dx
```

## 6. 最小二乘法

最小二乘法用于处理这种问题：

```text
A x ≈ b
```

如果没有精确解，就找一个 `x`，让误差最小：

```text
minimize ||A x - b||^2
```

在 IK 里，对应关系是：

```text
A -> J(q)
x -> dq
b -> dx
```

所以 IK 的一步可以写成：

```text
minimize ||J(q) * dq - dx||^2
```

意思是：找一个关节增量 `dq`，让末端运动尽量接近目标误差 `dx`。

## 7. 雅可比伪逆

如果 `J` 是方阵而且可逆，可以直接：

```text
dq = J^-1 * dx
```

但真实机械臂里 `J` 通常不是好处理的方阵：

- 7 自由度机械臂的 `J` 常是 `6 x 7`，未知数比方程多。
- 有些任务只控制位置，`J` 可能是 `3 x 7`。
- 机械臂可能接近奇异位形，`J` 不可逆或病态。

所以会用 Moore-Penrose pseudoinverse，伪逆：

```text
dq = J^+ * dx
```

`J^+` 可以理解为“非方阵情况下最接近逆矩阵的东西”。它给出一个最小二乘意义下的解。

常见含义：

- 如果无精确解，伪逆给误差最小的解。
- 如果有很多解，伪逆给范数最小的解，也就是关节动得相对最少的解。

NumPy 里常见写法：

```python
dq = np.linalg.pinv(J) @ dx
```

## 8. 阻尼最小二乘

普通伪逆在奇异位形附近可能很不稳定。一个小的末端误差可能导致非常大的关节变化。

所以机器人 IK 里经常用 damped least squares，阻尼最小二乘：

```text
dq = J.T * (J * J.T + lambda^2 * I)^-1 * dx
```

或者：

```text
dq = (J.T * J + lambda^2 * I)^-1 * J.T * dx
```

其中 `lambda` 是阻尼系数。

直觉上：

- `lambda` 越小，越接近普通伪逆，动作更直接，但奇异附近更容易炸。
- `lambda` 越大，动作更保守，更稳定，但收敛可能更慢。

## 9. 一个典型 IK 迭代流程

IK 通常不是一步完成，而是循环迭代：

```text
1. 当前关节 q
2. 用 FK 算当前末端位姿 T_current
3. 计算目标位姿和当前位姿的误差 dx
4. 计算当前 q 下的雅可比 J(q)
5. 用伪逆或阻尼最小二乘求 dq
6. q = q + alpha * dq
7. 检查误差是否足够小，否则继续
```

伪代码：

```python
for _ in range(max_iter):
    T_current = fk(q)
    dx = pose_error(T_target, T_current)
    if np.linalg.norm(dx) < tolerance:
        break

    J = compute_jacobian(q)
    dq = np.linalg.pinv(J) @ dx
    q = q + alpha * dq
```

其中 `alpha` 是步长，用来避免一次更新太猛。

## 10. 常见坑

### qpos 顺序不一定等于你脑中的关节顺序

`qpos[i]` 对应哪个关节，由 MJCF/URDF 解析后的模型顺序决定。写代码时最好打印 joint name 和 qpos index 的对应关系。

### 位置和姿态误差单位不同

位置误差单位是 m，姿态误差单位通常是 rad。直接把它们拼成 6 维误差时，经常需要加权：

```text
error = [position_error, rotation_weight * orientation_error]
```

### 雅可比的参考坐标系要一致

有的雅可比是 world frame，有的是 local frame。`dx` 和 `J` 必须在同一个坐标系下，否则更新方向会不对。

### 奇异位形会放大关节速度

接近奇异位形时，伪逆可能给出很大的 `dq`。实际代码里通常会：

- 加阻尼。
- 限制 `dq` 最大值。
- 限制关节角范围。
- 降低步长 `alpha`。

### FK 比 IK 更基础

先确认 FK 对，再做 IK。因为 IK 每一步都依赖 FK 和 Jacobian。如果 FK 的 frame、模型、q 顺序错了，IK 也会跟着错。

## 11. 和 Lesson 12 当前脚本的关系

当前 `check_fk_with_mujoco.py` 主要做 FK 对比：

```text
MuJoCo 当前 qpos
    -> Pinocchio FK
    -> KDL FK
    -> 打印末端 link7 的位姿矩阵
```

它还没有真正做 IK，但后续如果要做 IK，通常就会在这个基础上继续加入：

- 目标末端位姿 `T_target`
- 当前末端误差 `dx`
- 雅可比矩阵 `J`
- 伪逆或阻尼最小二乘
- 迭代更新 `qpos`

可以把当前脚本看成后续 IK 的地基：先验证模型、frame 名字、`qpos` 顺序、FK 结果是否一致。
