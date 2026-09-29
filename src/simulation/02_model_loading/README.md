# 3：从 MJCF 到可用模型

本文行数：84行，预期阅读时长：5分钟

**XML 是模型描述，`MjModel` 是编译后的模型，`MjData` 是一次仿真的可变状态。**

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

这里的“编译”是把模型描述整理成 MuJoCo 计算需要的数据结构，不是生成 Python 或 C++ 程序。按本模型的配置，编译器会由 geom 的形状和质量推导刚体惯性，并把 actuator 的关节名称关联到关节索引。流程依据[官方模型说明](https://mujoco.readthedocs.io/en/stable/modeling.html)与[Python 接口说明](https://mujoco.readthedocs.io/en/stable/python.html)；stable 页面会更新，仓库历史实测版本仍以验证记录为准。

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

**结果：** 自带模型包含一根有铰链的杆和一个自由漂浮的标记球。球仅用于说明自由关节的状态维度，关闭接触，在重力下下落；不与杆连接。编译后 `nq=8, nv=7, nu=1`，含义见[下一章](../03_state_step/README.md)。

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

## 外部机械臂模型怎样接入

Panda 可从官方 [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie/tree/main/franka_emika_panda) 获取。下载完整仓库或带齐依赖的模型目录，保留许可证，记录所用 commit SHA；`main` 会变化，不能作为精确版本号。

从 `franka_emika_panda/scene.xml` 加载场景，或按目标选择机器人入口 `panda.xml`；显式传入本机路径，例如 `Path(args.model).expanduser().resolve()`。不要复制旧脚本里的私人绝对路径，也不要假定前七个 `qpos` 永远都是机械臂关节。

本次实测范围是自带小模型，未把外部 Panda 加载或控制标为验收通过。旧材料见[清点记录](../mujoco/materials.md)。

## 出错时查

| 现象 | 优先检查 |
| --- | --- |
| 找不到 XML | 入口路径是否依赖当前工作目录 |
| 找不到 mesh | include、meshdir 与资产是否完整 |
| 编译失败或行为异常 | 错误行、单位、惯性合法性和 MuJoCo 版本 |

资料：[MuJoCo 3.8.1 Python](https://mujoco.readthedocs.io/en/3.8.1/python.html)；固定依赖与运行命令见[验证记录](../mujoco/verification.md)。

[上一章：机器人模型](../01_robot_models/README.md) · [返回目录](../README.md) · [下一章：状态与步进](../03_state_step/README.md)
