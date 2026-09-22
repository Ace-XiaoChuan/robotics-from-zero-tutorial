# Lesson 1 实现检查记录

本文行数：39行，预期阅读时长：2分钟

## 结论

2026-09-20 在 ROS 2 Humble 环境完成干净构建和通信集成测试。`robot_interfaces` 能生成 C++ / Python 类型，`ros2_comm_demo` 的四个 C++ 节点均编译通过；17 个 pytest 场景全部通过。

## 实际检查

| 检查 | 结果 |
| --- | --- |
| 从 `.srv` / `.action` 生成接口 | 通过 |
| 编译 `battery_node`、`pose_node`、`task_manager_node`、`command_node` | 通过，无编译警告 |
| 默认 launch 从原点到 `(1.0, 0.5) m` | 通过，Action 返回 `arrived` |
| 取消任务、忙碌时拒绝新目标、取消后接受下一目标 | 通过 |
| 无状态、NaN、越界、低电、错误坐标系、过旧/未来时间戳、NaN 位姿 | 均按设计拒绝 |
| 位姿或电量过期、低电、任务超时 | 均中止并发布零速度 |
| 客户端早于服务端启动 | 在等待期限内成功重试 |
| 速度命令停止 | 位姿节点在 watchdog 到期后停止积分 |
| 客户端结果超时 | 请求取消且不重复发送目标 |

测试使用独立 namespace、`ROS_LOCALHOST_ONLY=1` 和隔离的 ROS domain，不连接真机。它验证的是本课二维运动学通信模拟，不证明真实导航、动力学控制或急停能力。

## 复现命令

从仓库根目录执行：

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src/ros2/examples/communication --packages-up-to ros2_comm_demo
source install/setup.bash
colcon test --packages-select ros2_comm_demo
colcon test-result --verbose
```

本次检查曾遇到默认 `build/ros2_comm_demo` 残留了另一个同名包的 CMake cache；验证时改用 `/tmp` 下独立的 build/install/log 目录，没有删除用户的既有构建产物。这是构建目录复用问题，不是 Lesson 1 的源码依赖问题。

[返回课程入口](README.md) · [接口与实现说明](ros2_interfaces_notes.md)
