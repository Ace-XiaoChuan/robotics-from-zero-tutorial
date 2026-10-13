# 03：QoS、Executor 与组件

本文行数：96行，预期阅读时长：5分钟

**QoS 决定消息交付规则，Executor 决定回调何时执行；同进程、能通信和能及时处理数据是不同的问题。**

## 速记：把消息经过的环节分开看

```text
发布者产生消息 → 中间件传递与缓存 → 订阅回调得到执行 → 更新业务状态
                  ↑ QoS 规则         ↑ Executor 与回调组
```

即使消息已经到达，处理它的回调也可能还在等待。此时缓存中的机器人状态可能仍旧，不能只检查网络或只增加队列。

## 例子 1：类型相同，却无法通信

QoS（Quality of Service）是一组交付策略。基础复习先记住三类：

| 策略 | 问的是什么 | 典型选择 |
| --- | --- | --- |
| Reliability | 传输失败时如何处理 | `reliable` 尝试可靠交付；`best_effort` 允许丢失 |
| History / Depth | 缓存多少条样本 | `keep_last` 下深度 N 表示最多保留最近 N 条 |
| Durability | 晚加入者是否能取得已发布的保留样本 | `volatile`：只接收建立连接后的新样本；`transient_local`：发布者保留样本，可补给晚加入的兼容订阅者 |

**输入：** 发布和订阅的名称、类型及其他匹配条件都满足，只改变可靠性设置。

| 发布端提供 | 订阅端要求 | 可靠性是否兼容 |
| --- | --- | --- |
| `best_effort` | `best_effort` | 是 |
| `best_effort` | `reliable` | 否 |
| `reliable` | `best_effort` | 是 |
| `reliable` | `reliable` | 是 |

**解释：** 发布者提供的能力必须满足订阅者要求。某个可靠订阅者连不上，并不妨碍同话题的另一个尽力交付订阅者接收。`reliable` 也不意味着零延迟、无限缓存或绝不发生业务数据丢失。[Humble QoS 文档](https://raw.githubusercontent.com/ros2/ros2_documentation/humble/source/Concepts/Intermediate/About-Quality-of-Service-Settings.rst)

## 例子 2：深度是 10，为什么看不到之前的电量

**教学条件：** 发布者已经发送 `99、98、97`，随后订阅者才建立连接，双方使用 `volatile`。

**预期结果：** 不补发这三条历史消息；连接建立并正常处理后，可能从后续的 96 开始看到数据。深度 10 不是一份给所有未来订阅者准备的永久历史档案。

需要晚加入者取得保留样本时，双方应使用兼容的 `transient_local`，实际可取到的范围还受历史深度和发布者生命周期等条件限制。完整过程记录则交给 rosbag2。

## 例子 3：收到消息与执行回调不是同一时刻

**消息到达，只表示有数据可以处理；Executor（执行器）负责安排线程，真正调用处理数据的回调函数。** 这里的执行器是软件机制，不是驱动关节的电机执行器（actuator）。

例如，订阅关节状态时，你注册了一个更新 `current_position` 的回调。消息到达后，这个变量不会自动更新，必须等回调执行到赋值语句。

```text
注册回调 → 消息到达，订阅就绪 → Executor 在执行约束允许时调用回调 → 更新变量
```

`executor.add_node(node)` 把节点交给 Executor 管理；`executor.spin()` 让它持续等待并处理订阅消息、定时器到期等工作。“决定何时执行”不是承诺精确时刻，还要看线程是否空闲、回调组是否允许执行，以及其他就绪工作的调度。

**教学条件：** 单线程 Executor 中，A 回调在 `t=0 s` 开始，占用线程 `0.5 s`；B 的消息在 `t=0.1 s` 到达。

```text
时间： 0 s       0.1 s                        0.5 s
A：    [------------- 回调运行 ----------------]
B：              消息到达，等待                 最早此后执行
```

**结果：** B 至少等 `0.4 s` 才可能开始处理，其他就绪任务还可能增加等待。即使 QoS 完全兼容，也不能靠传输可靠性消除这段调度延迟。

**原因：** 单线程 Executor 只有一条执行线程，不会因为 B 的消息到达就暂停 A、转去执行 B。即使 A 只是在 `sleep()`，也会占住这条线程。因此，定时器设置每 `10 ms` 到期，也不保证回调精确地每 `10 ms` 开始执行。

如果 A 一直同步等待“由同一 Executor 处理的服务响应”，还可能形成互相等待。优先让回调短时间返回，通过异步响应继续处理，而不是在回调里长时间占住线程。

## 多线程为什么不一定解决问题

回调组（callback group）给回调增加并发约束：

| 回调组 | 允许怎样执行 |
| --- | --- |
| `MutuallyExclusive` | 同组回调不能同时执行 |
| `Reentrant` | 同组回调允许并行，包括同一回调的多次调用 |

默认组是互斥组。即使换成多线程 Executor，同一默认组的回调仍不能并行；不同组才可能并行，同组也可明确选可重入，但要自己处理共享数据安全。更多线程并不自动消除阻塞或数据竞争。[Humble 回调组说明](https://raw.githubusercontent.com/ros2/ros2_documentation/humble/source/How-To-Guides/Using-callback-groups.rst)

## 例子 4：Lesson 2 到底组合了什么

[主程序](../examples/composition/lesson2_composition/src/intra_process_pubsub.cpp)在一个进程中创建 Talker 和 Listener，将两者加入 `SingleThreadedExecutor`，并设置 `use_intra_process_comms(true)`。

**源码结论：** 两个节点共用一个进程，Executor 回调仍逐个执行。发布端用 `unique_ptr` 传递消息，订阅端接收 `UniquePtr`，代码还打印地址，意图观察消息传递。

这个主程序采用手动组合入口；Talker 和 Listener 的源码还各自使用 `RCLCPP_COMPONENTS_REGISTER_NODE`，CMake 也注册了两个组件，因此同一组节点定义还提供容器加载入口。容器需要实际构建并安装的共享库，本地 `add_library()` 未显式指定 `SHARED`，构建时需启用 `BUILD_SHARED_LIBS=ON`，详见[组件案例说明](../examples/composition/lesson2_composition/README.md)。

启用进程内通信也不能单凭开关就宣称所有路径都零拷贝，具体数据传递与性能要结合实际测量。本章没有容器加载或性能测量结果。

Lesson 1 的各个程序使用 `rclcpp::spin()` 的单线程执行器。Action 任务由每 `0.05 s` 触发的定时器逐步检查、发布速度和反馈，不另起分离线程；每次回调返回后，状态订阅、查询和取消仍有执行机会。单线程不保证实时性，慢回调仍会增加控制与取消延迟。详见[执行实现](../examples/communication/ros2_interfaces_notes.md#execution)与[通信检查记录](../examples/communication/verification.md)。

本章时序为教学示意，案例结论来自静态源码分析；执行器背景参照 [Humble Executor 文档](https://raw.githubusercontent.com/ros2/ros2_documentation/humble/source/Concepts/Intermediate/About-Executors.rst)。

[返回目录](../README.md) · [下一章：TF 与时间](../04_tf_time/README.md)
