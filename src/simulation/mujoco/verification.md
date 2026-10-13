# MuJoCo 小模型：配置与数值结果

本文行数：38行，预期阅读时长：2分钟

## 模型与环境

使用本仓库 [pendulum.xml](models/pendulum.xml)，包含单摆和自由关节球，无外部网格。运行环境为 Python 3.10.12、MuJoCo 3.8.1、NumPy 2.2.6，Linux，无窗口，依赖版本见 [requirements.txt](requirements.txt)。

模型步长 `0.002 s`，Euler 积分，重力 `(0, 0, -9.81) m/s²`。hinge 初始角 `0.5 rad`、初始速度零，motor 输入 `0.2 N·m`，运行 100 步。球无接触，按默认自由关节位置初始化。

## 实际结果

| 检查 | 结果 |
| --- | --- |
| nq / nv / nu | 8 / 7 / 1 |
| q=0.5 rad 时尖端坐标与解析式比较 | 最大绝对误差 0 m |
| ctrl=3 时的 motor 限幅 | actuator_force=2 N·m，ctrl 仍为 3 |
| 100 步后的时间 | 0.20000000000000015 s |
| 100 步后的 hinge 角 | 0.3059700872639505 rad |
| 两次 reset 后的轨迹最大绝对差 | 0 |
| 重置后的时间、速度和输入 | 恢复为 0，hinge 再设为 0.5 rad |
| 杆质量由 1 kg 改为 2 kg | 同构型尖端位置不变，惯量翻倍 |

初次加载时，`qpos=[0,1,0,1,1,0,0,0]`，`qvel` 七项与 `ctrl` 一项均为零，`time=0 s`；调用 `mj_forward` 后时间仍为零。

检查脚本使用 `<1e-12 m` 的解析位置误差、`<1e-12 s` 的末时刻误差和 `<1e-12` 的同字段重复轨迹差作为判据。名称映射与数组地址见[状态章](../03_state_step/README.md)。

## 复查命令

在安装了固定依赖的环境中，从仓库根目录运行：

```bash
python3 src/simulation/mujoco/check_basics.py
```

记录覆盖小模型加载、状态推进、限幅和重置。Panda 模型、Viewer 与渲染使用各自的案例入口。

[MuJoCo 目录](README.md) · [模型与仿真](../README.md)
