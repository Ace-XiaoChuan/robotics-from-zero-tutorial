# 05：状态、计算与时间步进

本文行数：239行，预期阅读时长：12分钟

**`mj_forward` 计算当前状态下的运动学和动力学结果；`mj_step` 内部同样会先做这项计算，再通过数值积分得到下一时刻的状态。**

## 开发者理解：先问是要观察当前状态，还是让系统运动一步

把单摆放在 `0.5 rad`，初始角速度为 `0 rad/s`，电机输入为零。我们可以提出两个问题：

- **此刻的杆尖在哪里，杆受到什么力，加速度是多少？** 调用 `mj_forward`，根据当前模型、状态和输入求出这些结果。
- **放开它，经过一小段时间后，角度和速度变成多少？** 调用 `mj_step`，它先计算上述动力学结果，再积分得到新的状态。

两者都会计算运动学和动力学。`mj_forward` 中的 forward 指正动力学的正向求解，不表示时间向前；它会计算加速度，但不会把加速度积成新的速度和位置。即使当前速度、加速度不为零，单独调用它也不会推进运动。

| 比较项 | `mj_forward(model, data)` | `mj_step(model, data)` |
| --- | --- | --- |
| 计算运动学：位置、姿态等 | 会 | 会，内部调用 `mj_forward` |
| 计算动力学：力、约束、加速度等 | 会 | 会，内部调用 `mj_forward` |
| 计算已配置的传感器输出 | 会 | 会，包含在计算流程中 |
| 数值积分，更新 `qpos`、`qvel` | 不做 | 做 |
| 推进 `data.time` | 不推进 | 前进一个 `model.opt.timestep` |

**`mj_step` 是“当前状态求值 + 时间积分”，而不是“比 `mj_forward` 多算一种动力学”。** 这里的“求值”是把模型、状态和输入代入计算流程。状态与派生结果的字段分类见[第 04 章](../04_model_data/README.md#mjdata-里哪些是状态哪些是计算结果)。状态也会随步进改变，不能把状态字段理解为静止量。

本章按自带单摆的 Euler 积分流程解释。更换为 RK4 等积分器时，内部还可能在中间状态多次求值；“计算当前动力学”和“积分推进状态”这两个职责仍然成立。上述关系可在[官方仿真流程](https://mujoco.readthedocs.io/en/3.13.0/programming/simulation.html#simulation-loop)与 [`mj_step` 源码](https://github.com/google-deepmind/mujoco/blob/3.13.0/src/engine/engine_forward.c)中核对。

## 速记：按要完成的任务选择调用

| 要完成的任务 | 调用方式 | 得到什么 |
| --- | --- | --- |
| 手动设置角度，检查当前杆尖位置或加速度 | 改状态后调用 `mj_forward` | 当前状态对应的派生结果，时间不变 |
| 让系统在力的作用下运动一步 | 调用 `mj_step` | 下一时刻的 `time`、`qpos`、`qvel` |
| 运动一步后，记录新角度对应的杆尖位置等结果 | `mj_step` 后调用 `mj_forward`，再读取 | 新状态及根据新状态重算的派生结果 |
| 连续模拟若干步，只在最后检查杆尖 | 连续调用 `mj_step`，最后调用 `mj_forward` | 省去中间各步结束后的额外求值 |

调用 `mj_step` 前，不要求用户先单独调用一次 `mj_forward`。它内部会完成所需计算；两者并非必须成对使用。为什么步后读取派生量时要额外求值，见下面的实际数据。

## 例子：只求值，单摆会不会动

本章使用 [pendulum.xml](../mujoco/models/pendulum.xml)：杆长 `0.5 m`，悬挂点在世界坐标 `(0, 0, 1) m`，零位时竖直向下，关节绕局部 `+y` 轴转动。模型还包含一个独立的自由球，用来说明数组维度；下面只观察杆的运动。

- `hinge` 是杆的转动关节，`data.joint("hinge").qpos[0]` 是角度，单位 rad；对应 `qvel[0]` 是角速度，单位 rad/s。
- `tip` 是杆尖的 `site` 标记点。它不增加质量或产生碰撞，`data.site("tip").xpos` 是其世界坐标 `(x, y, z)`，单位 m。

模型中 `tip` 定义在杆的 body 内：

```xml
<site name="tip" pos="0 0 -0.5" size="0.035" rgba="0.9 0.2 0.2 1"/>
```

这里的 `pos` 是杆自身坐标系中的局部位置。局部位置不变，世界位置随杆转动；坐标推导见[关节位置不等于工具尖端位置](../02_scene_objects/README.md#例子关节位置不等于工具尖端位置)。

下面代码从仓库根目录运行，不需要打开窗口：

```python
import mujoco

model = mujoco.MjModel.from_xml_path("src/simulation/mujoco/models/pendulum.xml")
data = mujoco.MjData(model)
mujoco.mj_forward(model, data)       # 根据零位计算一次初始结果

data.joint("hinge").qpos[0] = 0.5   # 只修改角度；速度和电机输入仍为零
print(data.site("tip").xpos)         # [0, 0, 0.5]：仍是零位的旧结果

mujoco.mj_forward(model, data)       # 用 0.5 rad 重新求值
print(data.site("tip").xpos)         # 约 [-0.239713, 0, 0.561209] m
print(data.joint("hinge").qacc[0])   # 约 -13.609863 rad/s²
print(data.time)                     # 0.0 s
print(data.joint("hinge").qpos[0])   # 0.5 rad
print(data.joint("hinge").qvel[0])   # 0.0 rad/s
```

这段代码中的数值已用 MuJoCo 3.13.0 / NumPy 2.2.6 无窗口核对，采用原模型重力、阻尼与零控制输入；下文也沿用同一配置。

`mj_forward` 计算出了非零加速度，证明它确实在进行动力学计算。但角度仍为 `0.5 rad`、速度仍为零、时间仍为零：它回答的是“此刻的加速度是多少”，尚未模拟这份加速度在一段时间内产生的运动。重复调用它，也不会让单摆自行摆下去。

手动设置 `qpos` 是把系统放到指定初态，适用于初始化和运动学检查；要观察电机或重力是否使系统运动，需要继续步进。

## 一个时间步里发生了什么

继续上面的例子，步前已经求值，时间为 `t0 = 0 s`，角度为 `q0 = 0.5 rad`，角速度为 `v0 = 0 rad/s`。模型步长为 `h = 0.002 s`。现在只调用一次：

```python
mujoco.mj_step(model, data)
```

本模型的一步流程如下，省略了数值有效性检查等实现细节：

```text
步前状态：t0、q0、v0，以及当前控制输入
    ↓ mj_step 内部调用 mj_forward
计算杆尖位置 p0、力、加速度 a0 等当前结果
    ↓ Euler 积分器推进状态
步后状态：t1 = t0 + h、新角度 q1、新速度 v1
    ↓ mj_step 返回
没有在返回前再完整求一次 p1、a1 等步后结果
```

先算受力和加速度，是因为积分器需要知道系统怎样加速，才能计算新的速度和构型。**`mj_step` 已经包含 `mj_forward`；步后额外调用 `mj_forward`，是对新状态再求一次值。**

### 对照实际读数，理解“不是同一时刻”

下面是同一次调用前后的实测读数，数字已四舍五入。第三列是在第二列的基础上，再执行一次 `mj_forward` 后读取的：

| 字段与单位 | `mj_step` 前，已求值 | `mj_step` 刚返回 | 再调用 `mj_forward` |
| --- | --- | --- | --- |
| `time` / s | 0 | 0.002 | 0.002 |
| hinge 的 `qpos` / rad | 0.500000000 | 0.499945686 | 0.499945686 |
| hinge 的 `qvel` / rad/s | 0 | -0.027156857 | -0.027156857 |
| hinge 的 `qacc` / rad/s² | -13.609862779 | -13.609862779 | -13.577075411 |
| tip 的世界 `x` / m | -0.239712769 | -0.239712769 | -0.239688937 |
| tip 的世界 `z` / m | 0.561208719 | 0.561208719 | 0.561195700 |

看中间一列：角度和速度已经改变，仿真时间也到达 `0.002 s`；但 `qacc` 和杆尖位置仍是步前算出的值。它们都存在同一份 data 中，却分别来自积分后与积分前。

**“不是同一时刻”指字段的计算来源不同，不是仿真退回了旧时刻。** `data.time` 是当前仿真时间，不会自动让所有字段重算，也不能作为每个字段都已刷新的保证。`MjData` 同时保存状态和计算过程中的结果，不能把任意阶段的整份 data 都看成已经同步好的观测快照。

再执行 `mj_forward` 时，角度、速度和时间保持在步后状态，仅重新计算派生结果。表中最后一列就能回答“在 `0.002 s` 的新状态下，杆尖在哪里，加速度是多少”。本例未配置传感器；其他场景中传感器的类型、坐标系和采样设置需结合[观察章节](../09_observation/README.md)读取，不能把所有传感器都当作即时位置。

### 为什么不在每一步末尾自动再求一次值

让步进函数在积分后再重算一遍，确实可以让读取更方便。但在这个流程中，步前求值用于推进运动，步后求值用于观察新状态，二者承担不同任务。只有要立即读取步后派生结果时，后一次完整求值才有必要。

例如，连续步进时原本是：

```text
第 1 步：求值(q0, v0) → 积分到(q1, v1)
第 2 步：求值(q1, v1) → 积分到(q2, v2)
```

如果第 1 步末尾自动增加一次求值，第 2 步开始时又会执行当前状态的计算。两步之间控制输入还可能改变，之前算出的力和加速度也未必能直接复用。从这个调用顺序可以看出，按读取需要额外求值，可以省去用不到的计算；这是对流程的解释，不要求读者为了使用 API 先掌握引擎优化。

## 实际使用：什么时候再调用 forward

下面沿用前面已加载的 `model` 和 `data`。若要每步记录新角度对应的杆尖位置，使用：

```python
mujoco.mj_step(model, data)          # 先运动一步
mujoco.mj_forward(model, data)       # 根据步后状态更新观测
t = float(data.time)
q = data.joint("hinge").qpos.copy()
tip_world = data.site("tip").xpos.copy()
```

这时 `t`、`q`、`tip_world` 属于同一份步后观测。`.copy()` 用于保留数值，因为命名访问返回的数组视图会随着后续计算改变。

如果只需连续运动 100 步，在最后查看杆尖位置，可以写成：

```python
for _ in range(100):
    mujoco.mj_step(model, data)
mujoco.mj_forward(model, data)
tip_world = data.site("tip").xpos.copy()
```

每一步的动力学由 `mj_step` 内部完成，不会漏掉；只省去了中间各步结束后、没有读取需求的额外求值。若只读取步后的 `qpos`、`qvel` 和 `time`，则直接读取即可，不需要为了这三个字段再调用 `mj_forward`。

控制器若依赖杆尖位置等派生反馈，也应在读取前确认它们已按当前状态更新；高级用法可通过 `mj_step1` / `mj_step2` 把计算分阶段，见[官方控制循环](https://mujoco.readthedocs.io/en/3.13.0/programming/simulation.html#simulation-loop)。本章示例直接设置 `ctrl`，没有注册控制回调；注册 `mjcb_control` 后，额外 `mj_forward` 也会触发该回调，需按实际回调行为安排调用。

## 原理与实现：加速度为什么还不是下一状态

对单个转动关节，正动力学可以概括成：

$$
a = f(q, v, u)
$$

`q` 是当前角度（rad），`v` 是角速度（rad/s），`u` 是控制输入，`a` 是角加速度（rad/s²）。模型提供质量、惯性、重力和阻尼等参数。`mj_forward` 计算这个动力学关系，同时计算所需的运动学和约束等中间结果；它没有执行时间积分。

为单独理解积分，先看一个忽略阻尼隐式处理的半隐式 Euler 教学关系：

$$
v_1 = v_0 + h a_0,\qquad q_1 = q_0 + h v_1,\qquad t_1 = t_0 + h
$$

其中 `h` 的单位是 s。第一式中 `s × rad/s² = rad/s`，得到速度增量；第二式中 `s × rad/s = rad`，得到角度增量。**求出 `a0` 与用它推进速度、位置，是两项不同的计算。**

本章实际模型含 `0.1 N·m·s/rad` 的关节阻尼，MuJoCo 的 Euler 默认对阻尼采用隐式处理。因此，上表的新速度不能简单用 `v0 + h * data.qacc` 精确复算；积分器内部还处理了阻尼的影响。表中的 `qacc` 是步前连续时间动力学的计算结果，也不是该积分区间平均加速度的记录。具体算法与数值误差见[动力学与控制：仿真步进](../../control/05_integration_step/README.md)及 [Euler 实现](https://github.com/google-deepmind/mujoco/blob/3.13.0/src/engine/engine_forward.c)。

步后再求出的加速度 `a1` 和力描述的是新状态，不会回头改变已经完成的运动。若要分析上一积分区间的受力，应在对应的动力学阶段保存结果；若要分析积分器实际采用的更新量，还要结合所用积分算法，不能把重算后的 `qacc` 当成历史记录。

## 按需查阅：状态数组与关节地址

### 本模型的数组维度

| 字段 | 长度 | 本模型中的含义 |
| --- | --- | --- |
| `data.qpos` | `model.nq=8` | hinge 角度 1 项 + 自由球位置 3 项和四元数 4 项 |
| `data.qvel` | `model.nv=7` | hinge 角速度 1 项 + 自由球线速度 3 项和角速度 3 项 |
| `data.ctrl` | `model.nu=1` | 一个 motor 的输入，不是关节状态；本例 gear=1，对 hinge 产生力矩 |
| `data.time` | 标量 | 仿真时间，单位 s |
| `data.site("tip").xpos` | 3 | tip 的世界坐标 `(x, y, z)`，单位 m |

### joint ID 不是数组起点

自带模型的编译结果可由[检查脚本](../mujoco/check_basics.py)核对：

| joint 名称 | joint ID | qpos 起点 / 长度 | qvel 起点 / 长度 |
| --- | --- | --- | --- |
| hinge | 0 | 0 / 1 | 0 / 1 |
| floating | 1 | 1 / 7 | 1 / 6 |

这里两个关节的 qpos 与 qvel 起点恰好相同，但若再增加一个 hinge，其 `qpos` 起点将为 8，`qvel` 起点为 7。不能用 `qpos[joint_id]` 作为通用读取方式：

```python
joint_id = model.joint("hinge").id
q_address = model.jnt_qposadr[joint_id]
v_address = model.jnt_dofadr[joint_id]
q = data.joint("hinge").qpos.copy()  # 按名称取得该关节的正确切片
```

### 含四元数的构型不能逐项积分

hinge 的一个角度对应一个角速度；球关节和自由关节的姿态用四元数表示，有 4 个分量、3 个旋转自由度。因此 `qpos` 与 `qvel` 不一定等长，不能对整个 `qpos` 简单差分得到通用速度，也不能直接执行 `qpos += h * qvel`。

比较含姿态的构型或按速度更新构型时，按需使用 `mj_differentiatePos`、`mj_integratePos`。MuJoCo 四元数顺序为 `(w, x, y, z)`，不能直接复制其他库的 `(x, y, z, w)`；线速度、角速度的参考系仍需按关节与接口的约定核对。

## 按需查阅：三种频率与两种时间

以下是[机械臂脚本](../mujoco/arm_walkthrough.py)采用的调度关系：

| 工作 | 仿真时间间隔 | 每仿真秒次数 |
| --- | --- | --- |
| 物理步进 | `0.002 s` | 500 |
| 更新控制输入 | 每 5 步，即 `0.010 s` | 100 |
| 同步显示 | 每 20 步，即 `0.040 s` | 25 |

两次控制更新之间，输入保持，物理状态仍逐步变化。显示可以跳过中间状态，物理步进不必跟着画面刷新频率走。本例 100 步推进 `0.2 s`，这里说的是仿真时间。

`data.time` 是仿真时间，电脑真实经过的时间叫墙钟时间。计算机可能花 `0.3 s` 或 `2 s` 跑完 `1 s` 仿真；`sleep()` 让程序等待，不会自行推进物理。轨迹按仿真时间定义时，用 `data.time` 计算目标。实时显示的节奏处理见[观察章节](../09_observation/README.md)。

## 参考资料

- [官方仿真流程、状态与正动力学](https://mujoco.readthedocs.io/en/3.13.0/programming/simulation.html)：核对 `mj_step` 内部调用及派生结果的计算阶段。
- [MuJoCo 3.13.0 的 forward、step 与 Euler 源码](https://github.com/google-deepmind/mujoco/blob/3.13.0/src/engine/engine_forward.c)：核对积分顺序、阻尼处理和回调。
- [site 定义](https://mujoco.readthedocs.io/en/3.13.0/XMLreference.html#body-site)与[本仓库验证记录](../mujoco/verification.md)。

[上一章：模型与数据](../04_model_data/README.md) · [返回目录](../README.md) · [下一章：控制输入](../06_actuation/README.md)
