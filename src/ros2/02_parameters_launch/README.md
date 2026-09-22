# 02：参数、名称与 launch

本文行数：96行，预期阅读时长：4分钟

**先找到正确的程序，再配置节点行为和通信名称；launch 将这些启动信息集中保存。**

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

Lesson 1 的自定义接口由同目录下的 `robot_interfaces` 包提供，业务包已显式声明 `rclcpp_action`、`rcl_interfaces`、消息和 launch 依赖；本仓库中的版本已完成干净构建与通信测试。

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

## 例子 3：参数改了，发布频率为什么没变

**教学设定：** 某节点声明了浮点参数 `publish_period_s`，启动时读取它来创建定时器。在上面的 `Node(...)` 中传入 `parameters=[{"publish_period_s": 0.5}]`。

**预期结果：** 若实现正确使用该值，目标周期为 `0.5 s`，对应 `1 / 0.5 = 2 Hz`；实际回调频率仍受调度影响。

运行中把参数改为 `0.2`，只是提出配置变更。即使参数更新成功，若代码没有据此重设定时器，定时器也可能仍按旧周期工作。节点还可以拒绝非正周期等无效值。

**现有源码的区别：** Lesson 1 电量节点把周期直接写成 `1000ms`，没有声明上述参数，所以添加这个配置并不能直接把现有节点变成可调频率节点。[Humble 参数说明](https://raw.githubusercontent.com/ros2/ros2_documentation/humble/source/Concepts/Basic/About-Parameters.rst)

## 启动顺序与“已经准备好”

launch 启动了服务端进程，不代表服务已注册、传感器已有有效数据。客户端需要等待服务可用，并规定超时或重试行为。

例如当前 Action 客户端在查找服务端之前就取消了发送定时器。如果这次等待失败，没有新的触发便不会自动重试。固定多睡几秒只是在押注启动速度，无法替代就绪条件。

## 按需查阅

- [原 launch](../examples/communication/ros2_comm_demo/launch/launch.py) · [构建配置与已知遗漏](../examples/communication/ros2_interfaces_notes.md#build)
- [工程基础中的构建速查](../../foundations/engineering/04_cpp_build/README.md)：不必为本章重学完整构建工具链。

本章新 launch 与参数场景是教学示例；已核对源码关系，未启动新增节点。

[返回目录](../README.md) · [下一章：QoS 与执行](../03_qos_executors/README.md)
