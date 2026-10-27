# 10：初始化、重置、记录与复现

本文行数：107行，预期阅读时长：5分钟

**重复实验要重置整份状态，固定模型、步长和输入，并说清记录的是步前还是步后。**

## 开发者理解：把一次实验的起点与时间说清楚

比较两个控制输入，需要让它们从相同初态开始。保存一段数据，还需要说明每行观察发生在动作之前还是之后。否则，两次轨迹不同可能来自旧速度未清空，图像和角度不一致也可能来自采样时刻不同。

初始化用于建立起点；重置用于回到某个起点；保存快照用于从中途续跑。三种用途需要的信息不完全相同。

## 速记

- `mj_resetData` 恢复模型默认状态，包括时间、速度和控制输入等；不是只把关节位置清零。
- 默认 `qpos` 来自模型的 `qpos0`，free joint 的默认姿态也应保持有效，不能把所有四元数分量清零。
- 设置初始状态后调用 `mj_forward`，让坐标等派生量与状态一致。
- NumPy 读取常得到底层数据的视图；历史记录要 `.copy()`，否则可能保留的只是不断变化的同一块内存。

## 例子：同一段输入执行两遍

检查脚本每次都执行下面的重置：

```python
mujoco.mj_resetData(model, data)
data.joint("hinge").qpos[0] = 0.5  # rad
mujoco.mj_forward(model, data)
```

**条件：** 默认初速度为零；固定步长 `0.002 s`，每步写 motor 输入 `0.2 N·m`，运行 100 步。除初始化外不覆盖 `qpos`。

**记录约定：** 第 k 次循环先写输入，再执行一步；记录步后 `time、qpos、qvel`。第一行时间为 `0.002 s`，末行为 `0.2 s`；这一行的输入是刚刚作用于前一个时间区间的命令，而不是下一步新命令。

**结果与解释：** 两次重置后的轨迹按相同列逐项比较；实际误差见[验证记录](../mujoco/verification.md)。这证明本模型在该环境和输入下可重复，不代表不同版本、硬件或任意接触场景都会逐位一致。示例的固定命令也不是反馈跟踪控制。

## 只重置 qpos 为什么不够

假设上一轮结束时杆仍有角速度。只把角度改回 `0.5 rad`，下一步它仍带着旧速度运动；如果控制器还有积分项、滤波状态或自己的随机数生成器，也要在应用层重置。`mj_resetData` 不会替你清空 Python 控制器对象。

若需从任意中途状态精确续跑，单存 `qpos/qvel` 未必够，还可能涉及 actuator 激活状态、输入和求解器历史。应按需要使用 `mj_getState/mj_setState` 及对应 state mask，另外保存应用层状态；这与“从初始条件重新跑一遍”不同。

## keyframe 怎样作为命名初态

[机械臂模型](../mujoco/models/planar_arm.xml)声明 `home`，给两个关节和两个位置目标都设置零值。载入后可以按名称重置：

```python
home_id = model.key("home").id
mujoco.mj_resetDataKeyframe(model, data, home_id)
mujoco.mj_forward(model, data)
```

该例重置后仿真时间、速度为零，`qpos=[0,0] rad`，`ctrl=[0,0] rad`。keyframe 提供状态参考值，不会执行“回零运动”。真机回零和沿轨迹返回初态是另外的执行过程。

`mj_resetData` 恢复 data，不会恢复你手工改过的 model 重力、力矩范围或步长。需要对照原参数时，应显式恢复参数或重新加载模型；也要重置应用层控制器、轨迹阶段和随机状态。

## 每行记录对应哪个区间

假设步长为 `0.002 s`。第 k 次循环在 `t_k` 写入命令 u_k，再推进到 `t_(k+1)`，最后记录新状态。记录行包含的是：

```text
步后时间 t_(k+1)
刚刚在 [t_k, t_(k+1)) 使用的命令 u_k
步后 q、v，以及按新构型重算的 site/传感器
```

因此，时间为 `0.002 s` 的第一行所带命令，是从 `0` 到 `0.002 s` 使用的输入。若控制只每 5 步更新，连续五行可能共享同一个命令。这不代表漏采样，而是输入在这段时间保持。

把图像和状态配对时也应使用同一次采样对应的仿真时间；渲染耗时不能代替图像采样时刻。图像对齐与 episode 动作定义继续见[数据采集](../../data_collection/README.md)。

## 历史记录需要保留副本

MuJoCo Python 的许多数组是底层内存的视图。把 `data.qpos` 直接 append 到列表，列表可能一直指向同一份变化中的数据。需要保留历史值时使用 `data.qpos.copy()`；只取一个 Python float 或构造新的记录数组也能独立保存数值。

图像、site 坐标与 sensor 数组同样要考虑所有权。检查方法很直观：继续步进后，旧记录应该保持原值，而当前 data 继续变化。

## 按需查阅：中途快照与恢复

在同一 model 下，可按需要选择 state mask。下面保存包含积分所需相关状态与输入的 `mjSTATE_INTEGRATION`，数组长度由 MuJoCo 计算：

```python
mask = mujoco.mjtState.mjSTATE_INTEGRATION
state = np.empty(mujoco.mj_stateSize(model, mask))
mujoco.mj_getState(model, data, state, mask)
# 后续若要恢复：
mujoco.mj_setState(model, data, state, mask)
mujoco.mj_forward(model, data)
```

模型、mask 和状态数组必须匹配；派生缓冲区通过计算重建。这个数组不会自动保存 Python 控制器对象、随机数生成器、控制更新相位或外部消息队列。若控制每 5 步更新，还需要恢复当前位于这 5 步中的哪一步。

检查脚本在固定输入的两关节模型中，从运行 50 步的快照恢复，再走 20 步，与原分支对应结果在 `1e-12` 容差内一致。完整 3 秒机械臂实验从 home 重新运行两次，轨迹逐项差为零。两项检查分别对应续跑与重跑，配置见[验证记录](../mujoco/verification.md)。

## 一份记录至少说明什么

| 项目 | 本例 |
| --- | --- |
| 来源与版本 | 仓库自带 MJCF；依赖版本见验证记录 |
| 关节顺序 | hinge，再 floating；分别按各自地址切片 |
| 单位与坐标 | 角度 rad，平移 m；自由关节约定见状态章 |
| 时间与输入 | 步后时间；前一积分区间保持 motor 命令 |
| 判据 | 数值有限、时间正确、重复误差逐列不超过 `1e-12` |

这里 rad、m、rad/s、m/s 分别比较，不把不同单位的误差相加。正式轨迹与 episode 采集留到 S8。

资料：[State API](https://mujoco.readthedocs.io/en/3.13.0/APIreference/APIfunctions.html#mj-getstate) · [状态与可重复性](https://mujoco.readthedocs.io/en/3.13.0/computation/index.html#the-state)

[上一章：观察仿真](../09_observation/README.md) · [返回目录](../README.md) · [下一章：排错](../11_debugging/README.md)
