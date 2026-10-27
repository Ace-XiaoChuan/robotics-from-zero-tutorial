# 02：参数、名称与 launch

本文行数：99行，预期阅读时长：5分钟

**先找到正确的程序，再配置节点行为和通信名称；launch 将这些启动信息集中保存。**

**交互演示：** [ROS 2 启动实验台](parameters_launch_lab.html) 可直接用浏览器离线打开。通过构建流程、名称解析、参数脉冲、launch 配方与就绪检查五个场景，比较漏构建／漏加载环境、名称不匹配、只读改参、条件启动、查询超时和结果未确认等情况；可暂停、拖动时间线、切换配置并点击图中对象查看说明。图中时刻为教学假设，不会启动 ROS 进程；两个可写参数模式是额外教学对照。

## 速记

| 工具或概念 | 负责什么 | 不会自动完成什么 |
| --- | --- | --- |
| `colcon build` | 组织包的构建 | 安装所有缺失依赖 |
| `source …/setup.bash` | 在当前终端加载已有安装环境 | 重新编译刚修改的代码 |
| `ros2 run` | 启动一个包中的可执行程序 | 自动启动它所需的所有其他节点 |
| `ros2 launch` | 按 launch 描述组织节点与配置 | 保证所有业务服务已经就绪 |
| parameter | 配置一个节点的行为 | 成为其他节点共享的全局变量 |
| namespace / remapping | 组织或改变 ROS 名称 | 转换数据单位、坐标系或消息类型 |

## 例子 1：从源码文件到运行中的节点

Lesson 1 的组织关系是：

```text
src/ros2/examples/communication/ros2_comm_demo/
├── package.xml                 # 包信息与依赖
├── CMakeLists.txt              # 如何编译、安装
├── src/command_node.cpp        # 源码
└── launch/launch.py            # 四个节点的启动描述
```

CMake 把 `command_node.cpp` 编成 `command_node`，安装后由 ROS 找到它。假设依赖齐全、已构建并加载正确环境：

```bash
ros2 run ros2_comm_demo command_node
```

**预期结果：** 启动程序 `command_node`，它在代码中创建的节点名却是 `command`，默认显示为 `/command`。修改 `.cpp` 后，仍需重新构建；只重新打开终端不会更新可执行程序。

Lesson 1 的自定义接口由同目录下的 `robot_interfaces` 包提供，业务包已显式声明 `rclcpp_action`、`rcl_interfaces`、消息和 launch 依赖；已有[干净构建与通信测试记录](../examples/communication/verification.md)。原 launch 默认使用 `lesson1` 命名空间，运行它时客户端节点名为 `/lesson1/command`。

## 例子 2：同一个程序，放进另一套机器人命名空间

下面是使用现有电量节点构造的 **launch 教学示例**，不替换原案例文件：

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package="ros2_comm_demo",
            executable="battery_node",
            name="battery_monitor",
            namespace="arm_a",
            remappings=[("battery_level", "battery_percent")],
        )
    ])
```

**预期解析结果：**

| 配置 | 结果 |
| --- | --- |
| `name` 与 `namespace` | 节点完整名为 `/arm_a/battery_monitor` |
| 源码相对话题名 `battery_level` | 重映射后发布到 `/arm_a/battery_percent` |
| 另一个节点仍订阅 `/battery_level` | 名称不一致，不会自动接到这里 |

没有重映射时，相对名 `battery_level` 会解析为 `/arm_a/battery_level`；绝对名 `/battery_level` 不随节点命名空间改变。**重命名节点也不会自动把普通相对话题名改成节点名的子路径。**

对第二台机器人使用 `arm_b` 命名空间，可以隔开同名接口。与 TF 相关的 `frame_id` 是消息里的字符串，不能指望 topic 命名空间自动给它加前缀。[Humble launch 组织示例](https://raw.githubusercontent.com/ros2/ros2_documentation/humble/source/Tutorials/Intermediate/Launch/Using-ROS2-Launch-For-Large-Projects.rst)

## 例子 3：启动参数与运行中改参有什么区别

**源码与教学配置：** Lesson 1 电量节点已声明浮点参数 `publish_period_s`，启动时读取它来创建定时器，默认值为 `0.2 s`。在上面的 `Node(...)` 中加入 `parameters=[{"publish_period_s": 0.5}]`，可以在启动时改用 `0.5 s` 周期。

**预期结果：** 若实现正确使用该值，目标周期为 `0.5 s`，对应 `1 / 0.5 = 2 Hz`；实际回调频率仍受调度影响。

**现有实现：** 公共辅助函数把应用参数设为 `read_only=true`，所以运行中修改 `publish_period_s` 会被拒绝，需要修改启动配置后重启节点。周期还会校验有限数值和不小于 `0.001 s`，非法值使节点报告配置错误并退出。

**一般情况：** 其他允许动态改参的节点，即使参数更新成功，若没有据此重设定时器，实际周期也可能保持旧值。是否可改、怎样影响行为，应结合节点实现判断。[电量源码](../examples/communication/ros2_comm_demo/src/battery_node.cpp) · [参数辅助函数](../examples/communication/ros2_comm_demo/include/ros2_comm_demo/common.hpp) · [Humble 参数说明](https://raw.githubusercontent.com/ros2/ros2_documentation/humble/source/Concepts/Basic/About-Parameters.rst)

## 启动顺序与“已经准备好”

launch 启动了服务端进程，不代表服务已注册、传感器已有有效数据。客户端需要等待服务可用，并规定超时或重试行为。

当前客户端每 `0.2 s` 检查 Service 和 Action 是否就绪，随后异步查询缓存状态；只有响应 `valid=true` 且没有已有任务时，才发送一次目标。状态请求 `2 s` 无响应会清理后重试，整个启动等待默认最多 `30 s`。已有[客户端先启动的测试记录](../examples/communication/verification.md)。

目标一旦发出就不自动重发；被拒绝或等待结果超时，也不会把同一运动请求重新提交。默认结果等待期限为 `20 s`，超时会尝试取消已知目标并报告结果未确认。就绪等待与运动重试是两种不同意图，固定延时无法替代这些检查。

## 按需查阅

- [现有 launch](../examples/communication/ros2_comm_demo/launch/launch.py) · [构建与启动参数](../examples/communication/ros2_interfaces_notes.md#build)
- [工程基础中的构建速查](../../foundations/engineering/04_cpp_build/README.md)：不必为本章重学完整构建工具链。

本章 `arm_a` 的 launch 和 `0.5 s` 周期配置是教学示例，未单独运行；原案例的构建、默认启动与客户端等待行为已有[检查记录](../examples/communication/verification.md)。

[返回目录](../README.md) · [下一章：QoS 与执行](../03_qos_executors/README.md)
