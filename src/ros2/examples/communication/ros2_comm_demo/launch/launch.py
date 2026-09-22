from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    namespace = LaunchConfiguration("namespace")
    arguments = [
        DeclareLaunchArgument("namespace", default_value="lesson1"),
        DeclareLaunchArgument("start_command", default_value="true"),
        DeclareLaunchArgument("target_x", default_value="1.0"),
        DeclareLaunchArgument("target_y", default_value="0.5"),
    ]
    nodes = [Node(package="ros2_comm_demo", executable=name,
                  namespace=namespace, output="screen")
             for name in ("battery_node", "pose_node", "task_manager_node")]
    nodes.append(Node(
        package="ros2_comm_demo", executable="command_node",
        namespace=namespace, output="screen",
        condition=IfCondition(LaunchConfiguration("start_command")),
        parameters=[{
            "target_x": ParameterValue(LaunchConfiguration("target_x"), value_type=float),
            "target_y": ParameterValue(LaunchConfiguration("target_y"), value_type=float),
        }],
    ))
    return LaunchDescription(arguments + nodes)
