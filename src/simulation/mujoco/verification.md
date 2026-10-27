# MuJoCo 教程：配置与验证结果

本文行数：69行，预期阅读时长：5分钟

## 自带模型与复查环境

十二章教程使用 [pendulum.xml](models/pendulum.xml)、[arm_scene.xml](models/arm_scene.xml)及其 [planar_arm.xml](models/planar_arm.xml)、[contact_box.xml](models/contact_box.xml)，无需外部模型或网格。当前固定依赖为 [requirements.txt](requirements.txt)：MuJoCo 3.13.0 / NumPy 2.2.6；实际运行解释器为 Python 3.10.12，Linux。

[check_basics.py](check_basics.py)核对单摆，[check_tutorial.py](check_tutorial.py)核对新增概念与对照，[arm_walkthrough.py](arm_walkthrough.py)提供完整的两关节运动。新增结果保存在 [results/tutorial_metrics.json](results/tutorial_metrics.json)。

## 单摆配置与结果

使用本仓库 [pendulum.xml](models/pendulum.xml)，包含单摆和自由关节球，无外部网格。原始结果来自 Python 3.10.12 / MuJoCo 3.8.1 / NumPy 2.2.6，无窗口，原固定依赖见 [requirements-3.8.1.txt](requirements-3.8.1.txt)。同一脚本在 MuJoCo 3.13.0 下重新运行，下表数值与判据均通过；原有结果保留。

模型步长 `0.002 s`，Euler 积分，重力 `(0, 0, -9.81) m/s²`。hinge 初始角 `0.5 rad`、初始速度零，motor 输入 `0.2 N·m`，运行 100 步。球无接触，按默认自由关节位置初始化。

### 实际结果

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

检查脚本使用 `<1e-12 m` 的解析位置误差、`<1e-12 s` 的末时刻误差和 `<1e-12` 的同字段重复轨迹差作为判据。名称映射与数组地址见[状态章](../05_state_step/README.md)。

## 新增教程的 8 组数值检查

| 检查组 | 配置与判据 | 实际结果 |
| --- | --- | --- |
| 模型组织与 data 独立性 | include、default 编译；两份 data 分别修改；传感器维度 | 两个关节、两个输入、5 个 sensor/7 个标量输出；阻尼均为 0.1；另一份 data 保持初态 |
| 几何与传感器 | 设置 `[0.5,-0.8] rad`，forward 前后核对 site、FK 与 sensor | 直接改 qpos 后 site 暂存旧值；forward 后 tip 约 `(0.637634,0.103114,0.3) m`，输出一致，时间不推进 |
| 执行器与限幅 | 单摆 gear=2、原始 ctrl=3；机械臂肩位置目标 0.5 rad | 单摆执行器力=2，关节力矩=4 N·m；肩伺服原始 20 N·m 被限为 8 N·m |
| 质量、惯性与重力 | 单摆质量 1/2 kg，速度为零；比较同力矩与纯重力 | 无重力时角加速度约 2.315014/1.157507 rad/s²；纯重力均约 -13.609863 rad/s²；同构型几何不变 |
| 接触支撑与过滤 | 0.2 kg 方块从中心 z=0.06 m 静置 1 s；支撑误差小于 0.01 N，高度误差小于 0.001 m | 有接触时中心约 0.0499733 m，4 点法向力合计约 1.962 N；关闭两侧掩码后无接触，中心约 -4.85481 m |
| 摩擦与滑动 | 静置后设 vx=1 m/s，再走 0.5 s；无摩擦使用 condim=1，有摩擦使用 condim=3、μ=0.6 | 两组都被正常支撑；分别滑动约 0.500000/0.084408 m，最终 vx 约 1/0 m/s |
| 快照与 keyframe | 固定输入走 50 步保存 INTEGRATION 状态，再走 20 步；恢复后重算；误差容差 1e-12 | 同状态续跑与原分支一致；历史副本不共享内存；home 恢复零角度、零速度、零输入和零时间 |
| 机械臂完整运动 | 物理 dt=0.002 s，每 5 步更新位置命令，共 1500 步；检查时间、FK、终点误差、重跑与弱执行器 | 正常最终最大关节误差约 4.83×10⁻⁶ rad（要求 <0.001）；FK 最大差 2.22×10⁻¹⁶ m（要求 <1e-12）；重跑差为零；弱执行器误差约 `[0.332042,-0.498148] rad` |

机械臂的 kp=40、kv=8、gear=1，正常单个输出限幅 ±8 N·m，对照改为 ±0.01 N·m；初态与全部目标相同。世界系 z 向上，两根杆在 z=0.3 m 的水平面内运动，重力不产生绕竖直关节轴的力矩。除初态或滑动初速度设置外，运动由执行器输入或接触与重力推进，没有连续覆盖 qpos。

末端几何差按 m 比较，角度差按 rad 比较；完整记录的相同字段重跑差为零。有限容差的重复性针对这些固定模型、版本与输入，跨平台或更复杂接触条件需重新核对。

## 图像与窗口

按照[观察章节](../09_observation/README.md)的 Renderer 用法，在导入前设置 `MUJOCO_GL=egl`，从命名相机 overview 生成初态和 3 s 末态的 RGB 图像。实际输出形状 `(240,320,3)`、类型 uint8，两帧有 2602 个像素位置改变，图像非全黑；渲染未改变 data.time。已查看末态图像，机械臂、杆尖和地面可见。临时图像保存在仓库外。

`arm_walkthrough.py --viewer` 已尝试启动，本机 X11 无法打开 DISPLAY=:0，GLFW 初始化失败。因此被动窗口的实际显示、相机交互与提前关闭行为尚未完成运行验证；EGL 离屏图像与无窗口物理运行已通过，不能用它们替代窗口验证。

## 复查命令

在安装了固定依赖的环境中，从仓库根目录运行：

```bash
python3 src/simulation/mujoco/check_basics.py
python3 src/simulation/mujoco/check_tutorial.py
python3 src/simulation/mujoco/arm_walkthrough.py --output /tmp/arm_trajectory.csv
```

检查脚本可添加 `--output /tmp/tutorial_metrics.json` 导出本机结果。历史控制章节继续使用其原版本依赖与验证记录；这里没有重跑外部 Panda、视觉估计或 ROS 桥接案例。

[MuJoCo 目录](README.md) · [模型与仿真](../README.md)
