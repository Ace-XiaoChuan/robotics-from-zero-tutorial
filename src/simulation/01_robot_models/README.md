# 01：机器人模型描述了什么

本文行数：50行，预期阅读时长：3分钟

**模型不仅决定机器人长什么样，还决定关节如何运动、状态如何解释，以及受力后怎样变化。**

## 速记

| 内容 | 含义 | 改变后的主要影响 |
| --- | --- | --- |
| URDF 的 link / MJCF 的 body | 刚体及其局部坐标系 | 结构与坐标层级 |
| joint | 刚体之间允许的相对运动 | 自由度、转轴、零位与限位 |
| visual / geom | 显示形状；MJCF geom 也可参与碰撞与惯性推算 | 外观或物理行为，取决于配置 |
| collision / 接触 geom | 碰撞检测使用的几何 | 能否穿过障碍、在哪里接触 |
| inertial | 质量、质心和惯量 | 重力、加速和转动响应 |
| 工具坐标系 / site | 用来读取或定义任务位置的参考系 | 末端目标与误差的含义 |

URDF 通过 joint 的 parent / child 连接 link；MJCF 通过嵌套 body 表达层级，joint 放在运动 body 内。没有 joint 的子 body 固定在父 body 上。URDF 不是完整仿真场景，导入 MuJoCo 后也不能假定控制器、接触参数与原系统一致。

## 例子：关节位置不等于工具尖端位置

**条件：** 本章使用[自带单摆模型](../mujoco/models/pendulum.xml)。世界系 z 轴朝上；杆的关节原点在世界坐标 `(0, 0, 1) m`，绕局部 `+y` 轴按右手规则转动。零位时，杆沿局部 `-z` 方向伸出 `0.5 m`，尖端 site 为 `(0, 0, -0.5) m`。

**几何推导结果：** 关节角 `q` 单位 rad，尖端的世界坐标为：

```text
x = -0.5 sin(q)
y = 0
z = 1 - 0.5 cos(q)
q = 0       → tip = (0, 0, 0.5) m
q = 0.5 rad → tip ≈ (-0.239713, 0, 0.561209) m
```

**解释：** body 原点一直在关节处，site 才是杆末端。控制“末端到某点”前，要先确定读取的是法兰、夹爪中心还是工具尖端（TCP）。仅名称叫 `end_effector` 并不能保证偏移正确。

## 例子：质量翻倍，位置会不会变

**条件：** 保持几何与关节角不变，仅把杆的 geom 质量从 `1 kg` 改为 `2 kg`，惯性由同一几何自动推算。

**结果与解释：** 同一 `q` 下尖端坐标不变，质量和惯量翻倍；动力学方程中的惯性与重力项变化。不能据此断言角加速度总会减半，因为重力矩也变了。若改的是杆长，尖端坐标与惯性通常都会改变。[验证记录](../mujoco/verification.md)核对了几何不变和惯量翻倍。

## 容易混淆的地方

- 长度使用 m、质量使用 kg、惯量使用 kg·m²；渲染的网格缩放不能代替整套物理参数的单位核对。
- joint 的轴在指定局部系中解释，不能直接当成世界轴。MJCF XML 的角度单位由 `compiler angle` 指定，本例明确为 radian；运行时 hinge 的 `qpos` 使用 rad。
- 关节限位约束允许的运动范围；碰撞模型约束接触，两者不能互相替代。仿真限位通常是求解器约束，不是简单把位置数组裁剪到边界。

资料：[URDF](https://docs.ros.org/en/humble/Tutorials/Intermediate/URDF/URDF-Main.html) · [MJCF body 与 joint](https://mujoco.readthedocs.io/en/3.8.1/XMLreference.html#body)

[上一章：控制流导读](../00_control_flow/README.md) · [返回 S3 目录](../README.md) · [下一章：模型加载](../mujoco/01_model_loading/README.md)
