from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(package="ros2_comm_demo", executable="battery_node"),
            Node(package="ros2_comm_demo", executable="command_node"),
            Node(package="ros2_comm_demo", executable="pose_node"),
            Node(package="ros2_comm_demo", executable="task_manager_node"),
        ]
    )
