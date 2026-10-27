# 04：从模型描述到运行中的仿真

本文行数：132行，预期阅读时长：7分钟

**XML 是模型描述，`MjModel` 是编译后的模型，`MjData` 保存一次仿真的状态、输入和计算结果。**

## 开发者理解：系统定义与本次运行分开

同一根杆可以从不同角度释放，比较不同输入的运动。杆长、质量和关节轴可以共用，但每次运行的角度、速度与时间需要分开。MuJoCo 用 model 描述这个系统，用 data 存放某一次运行的数据。

### `MjData` 里哪些是状态，哪些是计算结果

理解 `MjData` 时，可以先按用途把常用字段分成两类：一种可以称为“静止类型”，另一可以称为“计算类型”。静止类型更改后类似标量，立即就会更新；而计算类型需要进行一次 mj_forward 才会更新。

| 类型 | 典型字段 | 含义 |
| --- | --- | --- |
| 当前状态和输入 | `data.time`、`data.qpos`、`data.qvel`、`data.ctrl` | 系统现在处于什么状态、施加什么控制；其中 `ctrl` 是用户给出的控制输入 |
| 根据当前状态算出的结果 | `data.site("tip").xpos`、`data.qacc`、接触、力、传感器输出 | 在当前模型、状态和输入下，几何和动力学结果是什么；也称派生结果 |

例如，`qpos` 告诉我们“关节现在转到了哪个角度”，`site("tip").xpos` 则回答“这个角度下，杆尖在世界坐标系的哪里”。`qacc` 是根据当前构型、速度、受力和约束求出的加速度；把加速度积成下一时刻的速度，还需要数值积分。

这些字段虽然都放在同一份 data 中，却不会自动保持同步。把关节角改成 `0.5 rad` 后，`qpos` 立即变成新值，杆尖坐标可能仍是上次计算的值；调用 `mj_forward` 才会根据新状态重算派生结果，而 `time`、`qpos` 和 `qvel` 不会因此前进。`mj_step` 还会做数值积分，推进状态与时间。两种调用及步前、步后字段的对应关系见[下一章](../05_state_step/README.md#一个时间步里发生了什么)。

因此，读取一个字段时，不仅要知道它属于哪份 data，还要知道它是状态、输入还是计算结果，以及最近一次计算是否已更新它。

## 速记

- `MjModel` 保存结构、惯性、关节地址、执行器参数和步长等；不是每步重建。
- `MjData` 保存位置、速度、控制输入、接触和中间计算结果；同一模型可以创建多份独立 data。
- XML 中的 `<include>`、mesh 和 texture 也是模型依赖，不能只复制入口 XML。
- 本教程使用仓库自带模型，不依赖私人工作区；Panda 是后续模型对齐的扩展。

## XML 怎样变成 model 与 data

`from_xml_path()` 把“读取、解析和编译”封装在一次调用中；`MjData(model)` 则根据编译后的模型分配并初始化仿真数据。过程如下：

```text
MJCF XML + include / mesh 等依赖
    ↓ 读取、解析：识别 body、joint、geom、actuator 等描述
模型描述（内部 mjSpec）
    ↓ 编译：处理默认值、检查引用与参数，计算惯性，安排索引和数组长度
MjModel：供仿真计算使用的结构与参数
    ↓ MjData(model)：按模型尺寸分配数组、设置默认初态
MjData：qpos、qvel、ctrl、time 与计算缓冲区
    ↓ mj_forward(model, data)：根据初态计算派生量，不推进时间
可读取当前构型对应的位置、力等计算结果
```

这里的“编译”是把模型描述整理成 MuJoCo 计算需要的数据结构，不是生成 Python 或 C++ 程序。按本模型的配置，编译器会由 geom 的形状和质量推导刚体惯性，并把 actuator 的关节名称关联到关节索引。流程依据[官方模型说明](https://mujoco.readthedocs.io/en/3.13.0/modeling.html)与[Python 接口说明](https://mujoco.readthedocs.io/en/3.13.0/python.html)。

## 例子：加载本教程模型

以下片段放在 `src/simulation/mujoco/` 下的脚本中，与 [check_basics.py](../mujoco/check_basics.py) 一样按脚本位置找资源：

```python
from pathlib import Path
import mujoco

xml = Path(__file__).resolve().parent / "models" / "pendulum.xml"
model = mujoco.MjModel.from_xml_path(str(xml))
data = mujoco.MjData(model)
mujoco.mj_forward(model, data)  # 初始化当前构型对应的派生量，time 仍为 0
```

**结果：** 自带模型包含一根有铰链的杆和一个自由漂浮的标记球。球仅用于说明自由关节的状态维度，关闭接触，在重力下下落；不与杆连接。编译后 `nq=8, nv=7, nu=1`，含义见[下一章](../05_state_step/README.md)。

**解释：** 修改 XML 后需要重新加载才能生效。`model` 中部分数值可在运行时修改，但不要把它当作任意改变拓扑的接口；本教程比较参数时重新编译模型。

## 结果与解释：XML 字段去了哪里

以下对应关系来自自带 [pendulum.xml](../mujoco/models/pendulum.xml) 的静态推导；初态与数组维度已于 2026-09-25 用 MuJoCo 3.8.1 无窗口核对，见[验证记录](../mujoco/verification.md)。不需要执行代码即可理解。

| XML 中的描述 | 编译或初始化后的结果 |
| --- | --- |
| `<option timestep="0.002" .../>` | `model.opt.timestep = 0.002`，单位 s；`data.time` 初始为 0 s |
| `rod` 内的 hinge joint，轴为 `0 1 0` | 关节绕 rod 局部坐标系的 +Y 轴转动，占 1 个 qpos 和 1 个 qvel 分量 |
| `marker` 的 `<freejoint/>` | 占 7 个 qpos 分量（位置 3 + 四元数 4）和 6 个 qvel 分量 |
| `<motor ... joint="hinge"/>` | 建立执行器到 hinge 的传动关联，`model.nu=1`，分配长度为 1 的 `data.ctrl` |
| `marker` 的 `pos="1 0 1"` | 此处父体为 world，初始世界位置为 `(1, 0, 1) m`，进入自由关节的初始 qpos |

所以这个模型的 `data.qpos` 初始为 `[0, 1, 0, 1, 1, 0, 0, 0]`：第一项是 hinge 的 `0 rad`，随后是自由球的位置 `(1, 0, 1) m` 和单位四元数 `(w,x,y,z)=(1,0,0,0)`。长度为 7 的 `qvel` 和长度为 1 的 `ctrl` 初始均为零。**初始化不是把所有数组简单清零**，位置需遵循 `model.qpos0` 中的默认构型。

之后写 `data.joint("hinge").qpos[0] = 0.5` 是改变本次仿真的角度；XML 和模型中的关节轴、质量不会因此改变。读取该角度对应的尖端世界坐标前，需要再次调用 `mj_forward`；只有调用 `mj_step` 才推进仿真。创建 `MjData` 本身不会让机器人运动，也不会打开窗口。

## 例子：同一个模型，两种初态

下面沿用已加载的 model；仅初始化用于比较的状态，不推进时间：

```python
first = mujoco.MjData(model)
second = mujoco.MjData(model)
first.joint("hinge").qpos[0] = 0.5
mujoco.mj_forward(model, first)
mujoco.mj_forward(model, second)
```

**结果与解释：** first 的 hinge 为 `0.5 rad`，second 仍为默认 `0 rad`。first 的尖端约为 `(-0.239713,0,0.561209) m`，second 为 `(0,0,0.5) m`。修改 first 的输入和步进 first，不会推进 second。

两者共用 model。如果修改重力、步长等共享参数，它们之后的计算都会受影响。需要比较不同质量的系统时，本教程从不同参数的 XML 重新编译两份 model，便于明确比较条件。

## 改了什么，需要做什么

| 改动 | 接下来做什么 |
| --- | --- |
| 本次 data 的关节角或速度 | 更新计算后读取派生量；需运动时继续步进 |
| XML 中的结构、质量或参数 | 重新加载与编译，创建与新模型匹配的 data |
| 支持运行时修改的选项，如重力 | 修改后在下一次计算中生效；重置 data 不会替你恢复 model |
| body、joint、执行器数量或拓扑 | 通过模型描述修改并重新编译，不能只扩大某个 NumPy 数组 |

model 中某些派生常量依赖其他模型参数；任意直接修改质量或惯量不等同于重新编译。熟悉参数更新 API 前，采用重新加载的小型对照更容易核对条件。

## 外部机械臂模型怎样接入

来源、场景入口、资源组织与版本记录按[第三章](../03_mjcf_scenes/README.md)准备。程序显式接收本机模型路径，例如 `Path(args.model).expanduser().resolve()`，再交给 from_xml_path；避免复制旧脚本里的私人绝对路径。

加载后仍需核对关节名称和状态地址，不能假定前七个 qpos 永远都是机械臂关节。模型读入成功只表明定义可以编译，驱动含义和实际运动还要分别检查。

自带模型的数值见[验证记录](../mujoco/verification.md)，Panda 脚本的模型与路径说明见[实现说明](../mujoco/materials.md)。

## 出错时查

| 现象 | 优先检查 |
| --- | --- |
| 找不到 XML | 入口路径是否依赖当前工作目录 |
| 找不到 mesh | include、meshdir 与资产是否完整 |
| 编译失败或行为异常 | 错误行、单位、惯性合法性和 MuJoCo 版本 |

本章保留了原 3.8.1 的初态记录；小模型现已在 3.13.0 复查，结果相同。固定依赖与命令见[验证记录](../mujoco/verification.md)。

资料：[MuJoCo Python](https://mujoco.readthedocs.io/en/3.13.0/python.html)

[上一章：MJCF 场景组织](../03_mjcf_scenes/README.md) · [返回目录](../README.md) · [下一章：状态与步进](../05_state_step/README.md)
