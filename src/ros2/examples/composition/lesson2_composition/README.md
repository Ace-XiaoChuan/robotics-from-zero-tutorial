# Lesson 2：组件组合与进程内通信

本文行数：37行，预期阅读时长：2分钟

## 速记要点

- `Talker` 和 `Listener` 已在源码与 CMake 中注册为 ROS 2 节点组件；容器加载需要实际构建并安装对应共享库。
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

组件源文件进入 `lesson2_composition_lib`，主程序只链接该库，避免同一组定义被重复编译。每个组件使用 `RCLCPP_COMPONENTS_REGISTER_NODE`，CMake 还通过 `rclcpp_components_register_nodes()` 注册了两个组件类；独立程序的手动组合与组件容器加载使用同一组节点定义。

当前 `add_library()` 没有显式指定 `SHARED`，构建时需设置 `BUILD_SHARED_LIBS=ON`。本机 Humble 的组件注册宏要求目标为共享库，未启用该配置时会在 CMake 配置阶段报错。成功构建和安装共享库后，才能继续检查容器发现与加载。

需要构建时，从仓库根目录执行：

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src/ros2/examples/composition --packages-select lesson2_composition --cmake-args -DBUILD_SHARED_LIBS=ON
```

以上对应源码结构与本机 Humble 构建宏的核对，未运行组件容器加载或测量性能。是否真的减少拷贝、以及具体性能收益，需要在目标 ROS 2 发行版和运行环境中用运行时指标单独测量。
