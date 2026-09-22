# S3 数值验证记录

本文行数：52行，预期阅读时长：3分钟

2026-09-20 实际运行；这是实现参考，不是读者必做练习，也不代表个人掌握程度或 S5 控制验收。

## 环境与来源

- Python 3.10.12、MuJoCo 3.8.1、NumPy 2.2.6；Linux，无窗口。
- 模型：[pendulum.xml](models/pendulum.xml)，本仓库教学编写，没有外部网格或私有模块。版本随本仓库文件保存。
- 最终验证使用用户指定的 `~/mujoco-env/bin/python`；激活入口是 `~/mujoco-env/bin/activate`。模型与脚本均来自本仓库，不依赖另一项目的资产或自定义模块。
- 曾尝试在 `/tmp` 创建独立 venv 并安装依赖，但沙箱网络解析失败，联网安装自动审批又因服务限流拒绝。因此**新环境安装可复现性尚未验证**；不能以已有私人环境代替这一项证据。
- 固定依赖已调整为实际运行版本，见 [requirements.txt](requirements.txt)。官方链接按 3.8.1 提供；本次核对已安装 API 与实际行为，未在线逐页核对官方网页。

需要复现时，从仓库根目录使用独立环境：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r src/simulation/mujoco/requirements.txt
.venv/bin/python src/simulation/mujoco/check_basics.py
```

本次实际执行的是：

```bash
~/mujoco-env/bin/python src/simulation/mujoco/check_basics.py
```

## 配置与结果

模型步长 `0.002 s`、Euler 积分器、重力 `(0, 0, -9.81) m/s²`。初始 hinge 角 `0.5 rad`，速度零；motor 输入 `0.2 N·m`，运行 100 步。标记球无接触，按模型默认自由关节位置初始化。

检查判据预先写在[脚本](check_basics.py)中：解析位置误差 `<1e-12 m`，末时刻误差 `<1e-12 s`；重复轨迹按相同字段比较、最大绝对差 `<1e-12`（各字段保留自身单位），所有记录有限。关节角变化须超过 `1e-5 rad`，只证明状态推进，不判断控制跟踪优劣。

| 检查 | 实际结果 |
| --- | --- |
| nq / nv / nu | 8 / 7 / 1 |
| q=0.5 rad 时尖端坐标与解析式比较 | 最大绝对误差 0 m |
| ctrl=3 时的 motor 限幅计算 | actuator_force=2 N·m，原 ctrl 仍为 3 |
| 100 步后的时间 | 0.20000000000000015 s |
| 100 步后的 hinge 角度 | 0.3059700872639505 rad |
| 两次 reset 后的完整轨迹最大绝对差 | 0 |
| 重置后的时间、速度、输入 | 均恢复为 0，hinge 再设为 0.5 rad |
| 杆质量从 1 kg 改为 2 kg | 同构型尖端坐标不变，杆惯量翻倍 |

名称映射也由脚本输出：joint `hinge=0, floating=1`；actuator `hinge_motor=0`；body `world=0, rod=1, marker=2`；site `tip=0`。关节的 qpos / qvel 地址见[状态章](02_state_step/README.md)。

## 验证边界

已验证自带模型的编译、名称与维度、解析位置、控制限幅、时间推进、重置和同环境重复性。尚未验证独立环境安装、外部 Panda 模型、Viewer / 渲染、接触操作或闭环轨迹跟踪。S3 教程正文已补齐，完整机械臂集成和动力学控制应在后续阶段单独记录证据。

[返回目录](README.md) · [学习路线](../../../doc/learning-roadmap.md#s3)
