# 12：综合例子：读懂一段机械臂仿真

本文行数：114行，预期阅读时长：6分钟

## 开发者理解：解释一段完整的运动与它的结果

本例让两关节机械臂从零位出发，经过一段已知关节目标曲线，再保持在最终目标附近。你应能从场景找到关节与工具点，从执行器定义解释命令单位，从循环解释运动怎样产生，并从实际记录判断跟踪情况。

使用[仓库自建场景](../mujoco/models/arm_scene.xml)与[完整程序](../mujoco/arm_walkthrough.py)。无外部网格或辅助库；输入为关节位置目标，输出为实际角度、速度、末端位置与误差。下面先给出完整结果，再按需查程序。

## 模型、目标与时间约定

| 项目 | 本例设置 |
| --- | --- |
| 世界坐标系 | z 向上；肩关节原点 `(0,0,0.3) m` |
| 结构 | 上臂长 0.4 m、质量 1 kg；前臂长 0.3 m、质量 0.5 kg；惯性按胶囊几何推算 |
| 关节 | `[shoulder, elbow]`，均绕所在 body 的 +z 轴转动，角度单位 rad |
| 初态 | home：角度、速度和位置目标均为零 |
| 执行器 | 两个 position，gear=1，kp=40，kv=8，单个输出范围 `[-8,8] N·m` |
| 被动参数 | 每关节 damping=0.1 N·m·s/rad，armature=0.01 kg·m² |
| 目标 | 前 1 s 从 `[0,0]` 平滑过渡到 `[0.5,-0.8] rad`，随后保持 2 s |
| 调度 | 物理步长 0.002 s；每 5 步更新命令；窗口模式每 20 步同步显示 |
| 计算 | implicitfast，1500 步，共 3 s 仿真；轨迹依据 data.time |

胶囊几何（capsule geometry）是“一个圆柱体，两端各接一个半球”形成的三维形状，外形像胶囊药丸。

机械臂在世界系水平面内运动，重力不产生绕两个竖直关节轴的驱动力矩。arm geom 关闭碰撞，地面用于提供场景参照；接触行为用[方块例子](../08_contact_constraints/README.md)单独观察。

## 实际结果：到位与过程误差分别看

以下来自 Python 3.10.12 / MuJoCo 3.13.0 / NumPy 2.2.6 的无窗口物理仿真，完整小型结果见 [tutorial_metrics.json](../mujoco/results/tutorial_metrics.json)。

| 指标 | shoulder | elbow |
| --- | --- | --- |
| 最终目标 / rad | 0.5 | -0.8 |
| 3 s 时实际角度 / rad | 0.499998716 | -0.799995173 |
| 最终目标减实际 / rad | 1.284×10⁻⁶ | -4.827×10⁻⁶ |
| 全过程最大绝对跟踪误差 / rad | 0.161047 | 0.250366 |

关节最终已很接近目标，但过渡阶段仍有明显滞后。最终误差小，不能说明整个过程都紧贴轨迹。这里的最大误差比较每步刚作用的保持命令与步后实际角度；控制更新周期与记录时刻在下文说明。

tip 世界坐标最终约为 `(0.637634532,0.103114718,0.3) m`。对每一行实际关节角进行解析 FK，所得位置与 MuJoCo site 最大绝对差约 `2.22×10⁻¹⁶ m`；这核对了本模型的几何计算。两次从 home 重跑，轨迹逐项差为零。

## 从场景找到输入和输出

[入口场景](../mujoco/models/arm_scene.xml)定义仿真选项、默认属性与环境，include 的 [planar_arm.xml](../mujoco/models/planar_arm.xml)定义两级 body、执行器、传感器和 home。

shoulder_servo 关联 shoulder，elbow_servo 关联 elbow。程序按名称读取和写入，避免把“前两个数组元素”当作普遍规则。换模型时先检查名称、关节类型、执行器类型与传动，再建立映射。

tip 是前臂局部 `(0.3,0,0) m` 的 site。读取它的 xpos 得到世界坐标；读取 forearm 的 body 原点得到的是肘部位置，两者不会相同。

## 从循环理解运动

核心顺序如下，省略了窗口同步、锁与记录代码；完整实现见[源码](../mujoco/arm_walkthrough.py)：

```python
for step in range(1500):
    if step % 5 == 0:
        command = target(data.time)
        for name, value in zip(ACTUATORS, command):
            data.actuator(name).ctrl[0] = value
    mujoco.mj_step(model, data)
    mujoco.mj_forward(model, data)
    # 此时读取步后角度、速度和 tip 世界位置，保存独立记录
```

位置执行器根据目标与实际误差产生力矩，物理引擎再计算运动。除 home 初始化外，循环不覆盖 qpos。额外 forward 用于对齐积分后构型的 site 和传感器，不再推进时间。

每 5 个物理步更新一次命令，中间保持上次命令。例如在 `t=0.01 s` 计算的目标用于随后五个区间，直到 `t=0.02 s` 再更新。每行记录步后 time、前一区间使用的 command、实际 q/v 和重算后的 tip。

## 对照：同一目标，执行器太弱会怎样

仅把两个执行器的力矩范围改为 `[-0.01,0.01] N·m`，其他条件不变。3 秒时实际角度约为 `[0.167958,-0.301852] rad`，目标减实际约为 `[0.332042,-0.498148] rad`。

目标生成、输入赋值和物理步进都执行了，但驱动力太小，在本次规定时间内无法到位。这个对照由[检查脚本](../mujoco/check_tutorial.py)直接修改 actuator_forcerange 后运行；没有通过覆盖状态补齐结果。

## 按需查阅：目标曲线与几何核对

目标过渡使用五次曲线。令 s 为“仿真时间 / 1 s”裁剪到 `[0,1]`，则：

```text
h(s) = 10s³ - 15s⁴ + 6s⁵
q_target = h(s) × [0.5,-0.8] rad
```

它在两端的速度与加速度为零，避免直接跳变目标；实际命令还按 0.01 s 控制周期采样并保持。轨迹平滑性和反馈设计详见[控制章节](../../control/06_control_constraints/README.md)。

对于本模型两个角度 `[a,b]`，tip 世界坐标的几何式为：

```text
x = 0.4 cos(a) + 0.3 cos(a+b)
y = 0.4 sin(a) + 0.3 sin(a+b)
z = 0.3
```

这里长度为 m、角度为 rad，第二杆在世界平面中的总转角为 a+b。将 `[0.5,-0.8]` 代入，得到目标 tip 约为 `(0.637633971,0.103114153,0.3) m`。这核对的是给定关节构型的几何位置；若从末端目标反求关节角，应查[逆运动学](../../kinematics/05_inverse_kinematics/README.md)。

## 可选复现

阅读前面的结果已能完成复习。需要核对本机行为时，在仓库外环境安装[固定依赖](../mujoco/requirements.txt)，从仓库根目录运行：

```bash
python3 src/simulation/mujoco/arm_walkthrough.py
python3 src/simulation/mujoco/arm_walkthrough.py --output /tmp/arm_trajectory.csv
python3 src/simulation/mujoco/check_tutorial.py
```

有可用桌面显示时，可给第一个命令添加 `--viewer`。窗口模式按墙钟节奏接近实时播放，不改变固定物理步长；提前关闭窗口会输出 completed=false 与实际记录步数。交互拖动或改变运行设置会改变实验条件，固定结果以无窗口运行核对。

CSV 列名标明单位，顺序为时间、两项目标、两项角度、两项角速度、tip 三维世界坐标。临时轨迹放在 /tmp 或仓库外；仓库只保留关键结果。Viewer 与离屏渲染的验证情况见[记录](../mujoco/verification.md)。

资料：[Python 物理与显示接口](https://mujoco.readthedocs.io/en/3.13.0/python.html) · [执行器定义](https://mujoco.readthedocs.io/en/3.13.0/XMLreference.html#actuator)

[上一章：排错](../11_debugging/README.md) · [返回目录](../README.md) · [术语与操作速查](../mujoco/quick_reference.md)
