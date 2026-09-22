# 01：从 MJCF 到可用模型

本文行数：49行，预期阅读时长：2分钟

**XML 是模型描述，`MjModel` 是编译后的模型，`MjData` 是一次仿真的可变状态。**

## 速记

- `MjModel` 保存结构、惯性、关节地址、执行器参数和步长等；不是每步重建。
- `MjData` 保存位置、速度、控制输入、接触和中间计算结果；同一模型可以创建多份独立 data。
- XML 中的 `<include>`、mesh 和 texture 也是模型依赖，不能只复制入口 XML。
- 本教程使用仓库自带模型，不依赖私人工作区；Panda 是后续模型对齐的扩展。

## 例子：加载本教程模型

以下片段放在本主题根目录的脚本中，与 [check_basics.py](../check_basics.py) 一样按脚本位置找资源：

```python
from pathlib import Path
import mujoco

xml = Path(__file__).resolve().parent / "models" / "pendulum.xml"
model = mujoco.MjModel.from_xml_path(str(xml))
data = mujoco.MjData(model)
```

**结果：** 自带模型包含一根有铰链的杆和一个自由漂浮的标记球。球仅用于说明自由关节的状态维度，关闭接触，在重力下下落；不与杆连接。编译后 `nq=8, nv=7, nu=1`，含义见[下一章](../02_state_step/README.md)。

**解释：** 修改 XML 后需要重新加载才能生效。`model` 中部分数值可在运行时修改，但不要把它当作任意改变拓扑的接口；本教程比较参数时重新编译模型。

## 外部机械臂模型怎样接入

Panda 可从官方 [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie/tree/main/franka_emika_panda) 获取。下载完整仓库或带齐依赖的模型目录，保留许可证，记录所用 commit SHA；`main` 会变化，不能作为精确版本号。

从 `franka_emika_panda/scene.xml` 加载场景，或按目标选择机器人入口 `panda.xml`；显式传入本机路径，例如 `Path(args.model).expanduser().resolve()`。不要复制旧脚本里的私人绝对路径，也不要假定前七个 `qpos` 永远都是机械臂关节。

本次实测范围是自带小模型，未把外部 Panda 加载或控制标为验收通过。旧材料见[清点记录](../materials.md)。

## 出错时查

| 现象 | 优先检查 |
| --- | --- |
| 找不到 XML | 入口路径是否依赖当前工作目录 |
| 找不到 mesh | include、meshdir 与资产是否完整 |
| 编译失败或行为异常 | 错误行、单位、惯性合法性和 MuJoCo 版本 |

资料：[MuJoCo 3.8.1 Python](https://mujoco.readthedocs.io/en/3.8.1/python.html)；固定依赖与运行命令见[验证记录](../verification.md)。

[返回目录](../README.md) · [下一章：状态与步进](../02_state_step/README.md)
