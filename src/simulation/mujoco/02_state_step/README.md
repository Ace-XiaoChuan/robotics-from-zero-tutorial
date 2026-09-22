# 02：状态、索引与步进

本文行数：53行，预期阅读时长：2分钟

**`qpos` 描述构型，`qvel` 描述运动速度；`mj_forward` 更新计算结果，`mj_step` 才推进仿真时间。**

## 速记：数组里的数字是什么

| 字段 | 长度 | 本模型中的含义 |
| --- | --- | --- |
| `data.qpos` | `model.nq=8` | hinge 角度 1 项 + free joint 的位置 3 项和四元数 4 项 |
| `data.qvel` | `model.nv=7` | hinge 角速度 1 项 + free joint 的线速度 3 项和角速度 3 项 |
| `data.ctrl` | `model.nu=1` | 一个 motor 的输入，不是关节状态 |
| `data.time` | 标量 | 仿真时间，单位 s |
| `data.site("tip").xpos` | 3 | 尖端在世界坐标系的位置，单位 m |

free joint 的位置和线速度在世界系表达，四元数按 `(w, x, y, z)` 表示 body 相对世界的朝向，角速度在 body 局部系表达。hinge 的位置为 rad、速度为 rad/s；自由关节的平移速度为 m/s。四元数受单位长度约束，4 个分量只描述 3 个旋转自由度，因此 `nq` 可以不等于 `nv`。

## 例子：joint ID 不是数组起点

自带模型的编译结果如下，来自[检查脚本](../check_basics.py)：

| joint 名称 | joint ID | qpos 起点 / 长度 | qvel 起点 / 长度 |
| --- | --- | --- | --- |
| hinge | 0 | 0 / 1 | 0 / 1 |
| floating | 1 | 1 / 7 | 1 / 6 |

这里两个起点恰好相同，但若再接一个 hinge，其 `qpos` 起点将为 8，`qvel` 起点为 7。不能用 `qpos[joint_id]` 作为通用读取方式。

```python
joint_id = model.joint("hinge").id
q_address = model.jnt_qposadr[joint_id]
v_address = model.jnt_dofadr[joint_id]
q = data.joint("hinge").qpos.copy()  # 按名称取得正确切片
```

## 例子：修改角度后，末端位置为什么没更新

```python
data.joint("hinge").qpos[0] = 0.5
mujoco.mj_forward(model, data)
tip = data.site("tip").xpos.copy()
```

**结果：** 尖端约为 `(-0.239713, 0, 0.561209) m`；`data.time` 不变。`mj_forward` 根据当前状态更新运动学、力等派生量，但不积分到下一个时刻。直接写 `qpos` 后，旧的 `xpos` 不会自己同步。

执行一次 `mj_step(model, data)` 则计算动力学并积分；本模型步长 `0.002 s`，100 步推进 `0.2 s`。这与电脑实际用了多少秒无关。若要记录步后新 `qpos` 对应的 site 位姿，紧接着调用 `mj_forward` 再读取，避免混用不同计算阶段的数据。

**边界：** 直接设置 `qpos` 适用于初始化或运动学检查；仅凭这种移动不能证明电机驱动有效。

资料：[计算流程与状态](https://mujoco.readthedocs.io/en/3.8.1/computation/index.html) · [API](https://mujoco.readthedocs.io/en/3.8.1/APIreference/APIfunctions.html)

[上一章](../01_model_loading/README.md) · [返回目录](../README.md) · [下一章：控制输入](../03_control_inputs/README.md)
