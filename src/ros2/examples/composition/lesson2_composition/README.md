# Lesson 2：组件组合与进程内通信

本文行数：28行，预期阅读时长：1分钟

## 速记要点

- `Talker` 和 `Listener` 是可被组件容器加载的 ROS 2 节点组件。
- `lesson2_composition_lib` 只编译一次两个组件；`intra_process_pubsub` 只负责创建节点、配置 `SingleThreadedExecutor` 并运行。
- `NodeOptions::use_intra_process_comms(true)` 请求在同一进程内使用进程内通信路径。示例日志中的消息地址用于观察所有权转移，不能单独作为性能结论。

## 例子

主程序在同一进程中创建两个节点：

```cpp
rclcpp::NodeOptions options;
options.use_intra_process_comms(true);
auto talker = std::make_shared<learn_compose::Talker>(options);
auto listener = std::make_shared<learn_compose::Listener>(options);
```

`Talker` 每秒发布递增的 `std_msgs/msg/Int32` 到 `count`，`Listener` 收到后打印数值和当前消息指针地址。

## 结果与解释

构建时，组件源文件进入共享库，主程序只链接该库，避免同一组定义被重复编译。每个组件都通过 `RCLCPP_COMPONENTS_REGISTER_NODE` 注册，因此后续也可以交给 ROS 2 component container 加载。

本例验证的是代码结构和通信配置；是否真的减少拷贝、以及具体性能收益，需要在目标 ROS 2 发行版和运行环境中用运行时指标单独测量。
