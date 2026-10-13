# 04：TF、坐标系与时间

本文行数：88行，预期阅读时长：4分钟

**一个位置数值只有结合“在哪个坐标系、对应哪个时刻”才有明确意义；TF 帮助查询这些坐标系之间的变换。**

## 速记

- `header.frame_id` 声明数据参考系，不会自动转换数据或建立 TF。
- tf2 管理带时间的坐标变换。框架相连、方向正确、查询时刻有数据，才能完成所需转换。
- 消息时间戳应按生产者约定解释；采样时刻、发布时间、接收时间可能不同。
- 动态变换要与数据时间对齐；“最新”不一定适合旧图像。

## 例子 1：先看懂一棵 TF 树

假设机器人基座固定，相机刚性安装在末端：

```text
world
└── base                  固定关系：基座安装位置
    └── tool              运动关系：随机械臂关节运动
        └── camera        固定关系：相机相对末端的安装位姿
```

树中的箭头表示父子关系；每个子坐标系只有一个父坐标系，不能组成环。相机相对 tool 固定，不代表相机相对 world 固定。

| 关系 | 通常发布到哪里 | 内容 |
| --- | --- | --- |
| 固定变换 | `/tf_static` | 固定安装偏移，配合持久性让晚加入者取得 |
| 动态变换 | `/tf` | 随关节运动等变化的、带时间戳的变换 |

对于 URDF 机器人，`robot_state_publisher` 根据模型和 `/joint_states` 更新链路：固定关节发布静态变换，可动关节随状态更新。**它计算坐标关系，不发送电机控制命令。** [Humble robot_state_publisher 说明](https://raw.githubusercontent.com/ros/robot_state_publisher/humble/README.md)

## 例子 2：把相机中的点转到基座下

**教学输入：** 三维右手系 `base` 与 `camera` 的轴方向一致；相机原点在 base 中是 `[0.5, 0, 0.2] m`。在同一时刻，点的相机坐标是 `[0.1, 0, 0.3] m`。

约定 `T_base_camera` 是 4×4 齐次变换，将 camera 坐标转成 base 坐标；点变换可写为 $p_{base}=R_{base,camera}p_{camera}+t_{base,camera}$，其中 R 为无量纲 3×3 旋转矩阵，p、t 是以 m 为单位的三维列向量。

本例 R 为单位矩阵，所以：

```text
p_base = [0.1, 0, 0.3] + [0.5, 0, 0.2] = [0.6, 0, 0.5] m
```

**解释：** 改标签却不改坐标，会把 `[0.1, 0, 0.3]` 错当成 base 下的位置。真正变换要同时更新数值和参考系。

反向求相机坐标时，本例减去平移即可。一般存在旋转时应使用 $p_{camera}=R^T(p_{base}-t)$，不能只把平移取负。实际相机光学坐标的轴方向可能与基座不同，因此本例的“直接相加”有明确前提。

## 例子 3：查询方向怎么记

对 `base → tool → camera` 这条链：

$$
T_{base,camera}=T_{base,tool}\,T_{tool,camera}
$$

**读法：** 先将 camera 下的点转到 tool，再转到 base，右边的变换先作用。

Python tf2 的核心调用形式是 `lookup_transform(target_frame, source_frame, time)`。例如目标 `base`、来源 `camera`，取得的变换用于将 camera 中的数据转到 base。它返回变换，还需要用变换函数将它应用于点；不能把返回值本身当作目标点坐标。

链不存在时，等一会儿未必有用；若只是同一时刻的变换稍晚到达，有限时间的等待才可能解决。查询最新可用变换也不代表它等于当前真实时刻。参照 [tf2 查询接口](https://raw.githubusercontent.com/ros2/geometry2/humble/tf2_ros_py/tf2_ros/buffer.py)。

## 例子 4：时间晚了 0.2 s，会差多少

**教学条件：** 相机轴方向保持不变，沿 base 的 +x 方向以 `0.5 m/s` 平移。图像在仿真时间 `10.0 s` 采集，处理结束时为 `10.2 s`。

**推导结果：** 将采样点错误地结合 `10.2 s` 的相机变换，会引入 `0.5 × 0.2 = 0.1 m` 的 +x 偏差。应使用 `10.0 s` 的变换；若相机也旋转，误差还与目标距离有关。

同理，若状态时间是 `10.0 s`、当前时间是 `10.2 s`，状态年龄才可算为 `0.2 s`。这个减法要求同一时间基准，不能拿系统时间减仿真时间。

## 仿真时间与真实时间

| 时间来源 | 适合表达什么 |
| --- | --- |
| System time | 操作系统墙钟时间，可能被校时调整 |
| Steady time | 单调经过时间，适合度量真实等待时长 |
| ROS time | 未启用仿真时间时跟随系统时间；启用后由 `/clock` 驱动 |

`use_sim_time=true` 不会自动生成时钟，仍需仿真器或回放工具提供 `/clock`。暂停仿真时 ROS 时间可能停止，重置时可能向后跳；依赖它的缓存和超时逻辑应处理这些情况。[ROS 2 时钟设计](https://design.ros2.org/articles/clock_and_time.html)

Lesson 1 的位置节点使用 wall timer 触发、节点时钟盖章，积分和等待时长由 steady clock 度量。各节点在启动时要求 `use_sim_time=false`，传入 `true` 会报告错误并退出；运行中切换仿真时间也不受支持。这是独立的墙钟模拟，不能直接当作 `/clock` 驱动的仿真节点。

任务节点保留完整 `PointStamped`：接收时检查 `frame_id` 和生产者时间戳，缓存后用 steady clock 检查距上次接收的时长，Service 返回原 header 与接收年龄。对真实传感器，还要另行约定 header 表示哪个采样时刻，电量 `Int32` 本身则没有采样时间戳。

本章坐标与时序例子为教学推导；未搭建或运行上述 TF 链。已有源码说明见[位置消息语义](../examples/communication/ros2_interfaces_notes.md#topics)。

[返回目录](../README.md) · [下一章：记录与排错](../05_recording_debugging/README.md)
