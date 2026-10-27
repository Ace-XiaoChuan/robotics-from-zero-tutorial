# MuJoCo 术语、数据与常用操作速查

本文行数：67行，预期阅读时长：4分钟

本页用于读程序时快速回忆名词与职责。概念例子从[十二章目录](../README.md)进入；接口参数按安装版本查[官方 Python 文档](https://mujoco.readthedocs.io/en/3.13.0/python.html)与 [API](https://mujoco.readthedocs.io/en/3.13.0/APIreference/APIfunctions.html)。

## 中英文术语

| 术语 | 本教程中的含义 | 阅读入口 |
| --- | --- | --- |
| model / 模型 | 结构、惯性、执行器和计算选项等系统定义 | [04](../04_model_data/README.md) |
| state / 状态 | 当前构型、速度等；精确续跑需按 state mask 确定范围 | [05](../05_state_step/README.md)、[10](../10_reset_recording/README.md) |
| body / 刚体 | 携带局部坐标系与惯性的结构单元 | [02](../02_scene_objects/README.md) |
| joint / 关节 | body 与父 body 之间允许的相对运动 | [02](../02_scene_objects/README.md) |
| DOF / 自由度 | 独立运动方向；关节数量与自由度数量可不同 | [05](../05_state_step/README.md) |
| geom / 几何体 | 附属刚体的形状，可用于显示、碰撞与惯性推算 | [02](../02_scene_objects/README.md) |
| site / 站点 | 任务或传感器使用的参考位置与坐标系 | [02](../02_scene_objects/README.md) |
| frame / 坐标系 | 一个原点及其朝向；使用位姿前需明确参考对象 | [02](../02_scene_objects/README.md) |
| actuator / 执行器 | 将命令转换为力并通过传动作用到系统 | [06](../06_actuation/README.md) |
| transmission / 传动 | 执行器与关节、肌腱或其他对象之间的映射 | [06](../06_actuation/README.md) |
| contact / 接触 | 几何表面相遇时的关系及对应约束 | [08](../08_contact_constraints/README.md) |
| constraint / 约束 | 通过约束力限制运动，如接触、限位、等式关系 | [08](../08_contact_constraints/README.md) |
| sensor / 传感器 | 模型定义的命名输出，需核对量纲与参考系 | [09](../09_observation/README.md) |
| timestep / 物理步长 | 每个物理步推进的仿真时间，s | [05](../05_state_step/README.md) |
| wall-clock time / 墙钟时间 | 电脑真实经过的时间 | [05](../05_state_step/README.md) |
| keyframe / 关键帧 | 命名的参考状态与输入；本身不执行运动 | [10](../10_reset_recording/README.md) |

## 看到这些字段时先想到什么

| 字段 | 含义与核对项 |
| --- | --- |
| `model.nq / nv / nu` | 构型、速度与控制输入的标量维度；不能默认三者相等 |
| `data.qpos` | 广义位置；可同时含 m、rad 和无量纲四元数 |
| `data.qvel` | 广义速度；不能通用地用整个 qpos 逐项差分得到 |
| `data.ctrl` | 执行器输入；单位取决于类型与传动 |
| `data.time` | 仿真时间，s |
| `data.site("tip").xpos` | 该 site 的世界位置，长度 3，m；需已更新计算 |
| `data.sensor(name).data` | 指定传感器的正确切片，维度由 sensor 类型决定 |
| `data.actuator_force` | 执行器空间输出，尚需通过传动解释关节受力 |
| `data.qfrc_actuator` | 执行器映射到自由度上的广义力，长度 nv |
| `data.qfrc_applied` | 额外施加的广义力，会与其他力共同作用 |
| `data.qfrc_bias` | 重力、Coriolis 与离心等偏置项；需结合动力学方程的符号约定 |
| `data.ncon / contact` | 当前计算的接触数量及接触记录；接触记录不等于必有非零力 |
| `model.jnt_qposadr / jnt_dofadr` | joint 在 qpos / qvel 中的地址，joint ID 不是通用切片起点 |

## 常用操作的职责

| 操作 | 用于什么 | 推进时间 |
| --- | --- | --- |
| `MjModel.from_xml_path(...)` | 读取、解析、编译模型文件 | 否 |
| `MjData(model)` | 创建一次运行的数据与缓冲区 | 否 |
| `mj_forward(model, data)` | 根据当前状态、输入更新运动学与动力学计算 | 否 |
| `mj_step(model, data)` | 计算并积分到下一时刻 | 是 |
| `mj_resetData(model, data)` | 恢复 data 默认状态 | 重置时间 |
| `mj_resetDataKeyframe(...)` | 从指定 keyframe 重置 | 使用关键帧时间 |
| `mj_getState / mj_setState` | 按 mask 保存或恢复状态 | 保存或恢复对应时间字段 |
| `mj_contactForce(...)` | 读取指定接触的力与力矩，使用接触坐标系 | 否 |
| `viewer.sync()` | 同步被动窗口的显示与交互状态 | 不代替物理步进 |
| `Renderer.update_scene / render` | 更新待渲染场景并生成图像 | 不代替物理步进 |

`mj_inverse` 根据指定状态与加速度计算所需广义力，接口用法见[正逆动力学](../../control/04_forward_inverse_dynamics/README.md)；它的输出不能不经映射就塞进任意 ctrl。

## 按问题找入口

“场景从哪里开始读”查 [03](../03_mjcf_scenes/README.md)；“数组是什么”查 [05](../05_state_step/README.md)；“命令为什么没有到位”查 [06](../06_actuation/README.md) 与 [11](../11_debugging/README.md)；“物体为什么滑或穿透”查 [08](../08_contact_constraints/README.md)；“保存的数据为什么变了”查 [10](../10_reset_recording/README.md)。

[返回目录](../README.md) · [完整机械臂程序](arm_walkthrough.py) · [验证记录](verification.md)
