# Lesson 1 源码阅读：状态、请求与任务如何配合

本文行数：146行，预期阅读时长：7分钟

本笔记对应重写后的 C++17 / ROS 2 Humble 代码。每个节点只承担一个主要职责；默认数据范围是 `map` 平面，坐标 m、速度 m/s，角度与姿态不参与本例。这里保留源码解释，通用概念见 [ROS 2 目录](../../README.md)。

<a id="concepts"></a>

## 1. 三种通信各自负责什么

Topic：电量、位置不断更新，速度命令驱动模拟点。Service：返回调用时最新缓存，不重新采样。Action：一次目标有接受、反馈、成功/中止/取消的生命周期。

位置节点真正响应 `cmd_vel`，因此 Action 目标与位置更新形成了闭环。`task_manager_node` 仍不负责底层动力学，只计算这个教学点的平面速度。

<a id="names"></a>

## 2. 名称与文件

| 类型 | 例子 |
| --- | --- |
| 包名 | `ros2_comm_demo` |
| 可执行程序 | `command_node` |
| 程序内节点名 | `command` |
| 默认完整节点名 | `/lesson1/command` |
| Action 名称 / 类型 | `/lesson1/navigation` / `robot_interfaces/action/Navigation` |

`Node("command")` 决定节点原始名称，namespace 由 launch 传入；所有通信名保持相对名称以便整体隔离。不要把类型 `Navigation` 的大写误写成实例名称。`std::shared_ptr` 用于保存 ROS 实体的生命周期；头文件里的 `SharedPtr` 只是对应指针类型的别名。

<a id="topics"></a>

## 3. Topic：数值、时间与接收有效性

| 名称 / 类型 | 语义 | 默认节奏 |
| --- | --- | --- |
| `battery_level` / `Int32` | 电量百分数，0～100 | 0.2 s 发布一次，初值 100，默认不递减 |
| `robot_pose` / `PointStamped` | `map` 中的三维点，z=0；节点发布时间戳 | 0.05 s 一次 |
| `cmd_vel` / `Twist` | 仅 linear.x/y 有效，map 中的 m/s | 任务运行时 0.05 s 一次 |

电量先发布再递减；设置 `drain_per_tick=1` 才会看到 `100、99、98…0`。`publish_period_s` 是启动参数，缓存深度 10 不代表 10 Hz。

位置节点按单调经过时间积分：`x += vx * dt`、`y += vy * dt`。新指令到达时先用旧速度结算上一段时间，防止把新速度追溯应用到过去。速度模长受 `max_speed` 限制，且积分不能越过最后指令的有效期。

任务节点只接受有限数值、z 近于 0、匹配 frame_id、有效且足够新的时间戳。缓存保留完整 header；除生产者时间外，也用 steady clock 检查位置和电量距离上次接收的时长。电量 `Int32` 没有采样时间戳，因此这里只能判断收到它有多久，不能证明真实电池测量的新鲜度。

<a id="services"></a>

## 4. Service：缓存值与“能不能用”分开

`GetRobotStatus` 请求为空，响应包括 `valid`、`battery_level`、完整 `pose`、两种接收年龄、`has_task` 和说明。

没有收到状态时，`valid=false`；未知电量为 -1，未知年龄为 -1 s。已有数值但过期也返回 `valid=false`，不能把缺数据解释成机器人就在原点。`valid=true` 只代表状态可用，不表示电量一定足够接受任务。

Service 响应中的电量与位置可能来自不同时刻；单线程回调读取保证这一操作中不会与其他 Executor 回调交错，但不代表传感器同时采样。

<a id="actions"></a>

## 5. Action：用定时器推进一个目标

```text
空闲 → 检查目标和状态 → 接受并占用任务槽 → 定时器反复推进
  ↑                                       │
  └──── 停止速度并释放槽 ← 成功 / 中止 / 取消 ┘
```

目标回调检查空闲、状态新鲜、电量、有限数值和工作范围；通过时立即占用任务槽，避免两个目标在 accepted 回调前同时通过。accepted 回调只保存 handle 和开始时间，不进入长循环。

每个 tick 依次检查：取消、状态过期、电量过低、任务超时、是否到达。通过后计算 `e = target − current`，速度为 `min(2.0, max_speed / ||e||) * e`；其中 2.0 的单位为 s⁻¹。到达判断先于除以距离，避免零距离除法。

反馈保存本次观测位置与剩余距离。终止时先发布零速度，然后调用 `succeed()`、`abort()` 或 `canceled()`，最后释放任务槽。结果 `final_distance` 是最后观测距离；状态失联时它不代表当前真实误差。

<a id="interfaces"></a>

## 6. 接口定义就在本课内

- [GetRobotStatus.srv](robot_interfaces/srv/GetRobotStatus.srv)：完整定义响应数据。
- [Navigation.action](robot_interfaces/action/Navigation.action)：目标、结果、反馈三部分。
- [接口包 CMake](robot_interfaces/CMakeLists.txt)：`rosidl_generate_interfaces()` 生成 C++ / Python 类型和类型支持。

例如 `.action` 中 `float64 target_x` 对应 C++ 的 `goal.target_x`，Action 的三个分段分别生成 `Goal`、`Result`、`Feedback`。字段名只能约定语义，范围和坐标校验仍要由节点实现。

这是为本次重写新建的协议：保留了任务目标字段，但 Service 不再用不带时间的独立 x/y/z 字段。旧笔记中接口缺失时给出的草案不再作为当前实现依据。

<a id="execution"></a>

## 7. 单线程为什么也能执行较长任务

`rclcpp::spin()` 使用单线程执行器。每次任务定时器只做一次检查与速度计算就返回，订阅、查询和取消回调仍有执行机会。这里不需要分离线程、互斥锁或原子占用标记；如果以后改为跨回调组并行，必须重新审查共享状态。

`[this]` 的 lambda 捕获允许回调访问节点成员。成员保存 Publisher、Subscription、Timer 等 ROS 对象，避免创建后立刻销毁。单线程不是实时保证，慢回调仍会拖延控制和取消。

客户端先等待服务可用，再异步查询；同一时刻最多一个状态请求，2 s 无响应就清理 pending request 后重试。`future.get()` 在响应已就绪的回调里调用，不在等待期间占住执行器。

默认启动等待最多 30 s。目标只发一次；拒绝不自动重试。默认结果等待最多 20 s，超时会尝试取消已知 handle 并停止等待重发逻辑，结果仍可能不确定。这个行为防止因网络问题重复执行运动目标。

<a id="build"></a>

## 8. 构建与参数边界

接口包先构建，业务包显式依赖 `rclcpp_action`、`robot_interfaces`、标准消息和参数描述类型；launch 的运行依赖也在 manifest 中列出。构建命令见[课程入口](README.md#需要运行时查)。

| 节点 | 常用启动参数与默认值 |
| --- | --- |
| battery | `initial_level=100`、`drain_per_tick=0`、`publish_period_s=0.2` |
| pose | `frame_id=map`、`max_speed=0.5`、`command_timeout_s=0.3`、`publish_period_s=0.05` |
| task_manager | `frame_id=map`、`max_speed=0.5`、`arrival_tolerance=0.03`、`state_timeout_s=0.8`、`task_timeout_s=15.0`、`min_battery=20`、`workspace_limit=5.0` |
| command | `target_x=1.0`、`target_y=0.5`、`startup_timeout_s=30.0`、`result_timeout_s=20.0` |

时间单位 s，位置阈值与工作范围单位 m，速度单位 m/s。共同 frame 必须一致。用户参数为只读启动配置，需修改后重启；默认时钟是系统时钟盖章、steady clock 度量时长，不支持运行中切换仿真时间。

<a id="issues"></a>

## 9. 旧问题怎样处理，仍有哪些边界

| 旧问题或容易误解之处 | 当前处理 |
| --- | --- |
| 接口包缺失、Action 依赖未声明 | 新接口包随仓库提供，构建依赖补齐 |
| 客户端 `Navigation`、服务端 `navigation` | 统一相对名称 `navigation` |
| 位置固定沿 x 递增，目标 `(5,3)` 无法到达 | 改为速度驱动的二维积分，默认目标 `(1,0.5)` |
| 发送前就取消定时器，服务端迟到后不再尝试 | 只在就绪并取得有效状态后发一次目标，等待设有期限 |
| 缓存初值冒充状态、丢弃 header | 区分未收到/过期，保留坐标与时间信息 |
| 分离线程退出与并发接单难管理 | 单线程定时器状态机，并在接受目标时占槽 |

仍不模拟碰撞、惯性、姿态、真实电池或网络安全。Twist 在此被约定为 map 轴速度，不应直接接到要求机体坐标速度的驱动器。异常退出时依靠接收端指令超时停止，正常终止则显式发布零速度。

<a id="experiments"></a>

## 10. 用结果回忆行为

- 状态查询返回 `valid=false`：即使位置字段显示零，也不能据此发送运动任务。
- Action 收到反馈：代表正在执行；必须等待最终结果才能区分成功、中止和取消。
- 新目标被拒绝：旧任务仍可能运行，拒绝不是对旧任务的取消。
- 结果等待超时：客户端不能确定结局，不自动重复目标。

<a id="review"></a>

## 11. 按问题查入口

[节点接口](../../01_nodes_interfaces/README.md) · [参数与启动](../../02_parameters_launch/README.md) · [QoS 与回调](../../03_qos_executors/README.md) · [TF 与时间](../../04_tf_time/README.md) · [记录与排错](../../05_recording_debugging/README.md)

<a id="references"></a>

## 12. 资料与实现证据

接口组织参考 [Humble 自定义 Action 教程](https://raw.githubusercontent.com/ros2/ros2_documentation/humble/source/Tutorials/Intermediate/Creating-an-Action.rst)；回调签名按本机 Humble 头文件核对。代码运行结果与自动检查范围单独保存在[实现检查记录](verification.md)，不作为读者作业。

[返回课程入口](README.md)
