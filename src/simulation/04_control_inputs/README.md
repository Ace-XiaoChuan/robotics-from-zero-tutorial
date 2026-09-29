# 5：ctrl 到底输入什么

本文行数：45行，预期阅读时长：2分钟

**`ctrl` 是执行器的命令数组；每项代表力矩、位置目标还是其他量，要看 actuator 的定义与传动。**

## 速记

| 接口或模型配置 | 含义 |
| --- | --- |
| `motor` | 直接驱动，输出还要经过 gear 等传动映射 |
| `position` | 位置伺服目标，内部由误差产生力，并非直接改位置 |
| `velocity` | 速度伺服目标，内部由速度误差产生力 |
| `data.qfrc_applied` | 外加广义力，长度 nv；绕开 actuator 的输入与传动路径 |
| `data.actuator_force` | 执行器空间的力 |
| `data.qfrc_actuator` | 执行器映射到自由度上的广义力 |

## 例子：一个可解释的电机输入

自带模型使用：

```xml
<motor name="hinge_motor" joint="hinge" gear="1"
       ctrllimited="true" ctrlrange="-2 2"/>
```

**条件与推导：** 这是直接驱动 hinge 的 motor，gear 为 1，无额外激活动力学；`ctrl=0.2` 对应施加 `0.2 N·m` 的关节力矩。正方向与 joint 的 `+y` 转轴一致。

**结果：** `ctrl=3` 超出范围时，正常启用控制限幅的计算使用 2，得到 `2 N·m`；但 `data.ctrl[0]` 本身仍可显示 3，不能只看输入数组判断实际输出。[检查脚本](../mujoco/check_basics.py)验证了这一点。

**解释：** 简单 hinge 的 gear 若改为 2，同一 motor 输入产生的关节力矩也变为两倍。对于 position actuator，简单 hinge 传动下目标对应的是 `gear × q`；只有 gear=1 等条件满足时，才能直接把输入读作关节目标角度。

## 例子：给目标位置，不会瞬间到位

教学配置 `<position joint="hinge" kp="20" gear="1"/>` 在不含其他执行器偏置和限幅影响时，产生类似 `tau = 20 × (ctrl - q)` 的弹簧力矩。若目标 `0.5 rad`、当前位置 `0.2 rad`，这一项为 `6 N·m`。

这只是某时刻的执行器力矩推导，实际加速度还受惯性、重力、阻尼与接触影响，目标也不保证达到。增益、稳态误差和跟踪曲线属于 S5。

## 旧脚本应怎样理解

旧 Panda 脚本通过 `qfrc_applied` 加力，与通过 `ctrl` 控制不是同一条路径。若模型自身的 actuator 同时产生力，两者会共同影响运动，必须一起核对。不能把“外加关节力运行了”写成“执行器控制已验证”。

资料：[Actuation model](https://mujoco.readthedocs.io/en/3.8.1/computation/index.html#actuation-model) · [actuator XML](https://mujoco.readthedocs.io/en/3.8.1/XMLreference.html#actuator)

[上一章](../03_state_step/README.md) · [返回目录](../README.md) · [下一章：显示与频率](../05_viewer_rendering/README.md)
