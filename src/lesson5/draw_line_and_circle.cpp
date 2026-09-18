#include <thread>
#include <memory>
#include <cmath>

#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.h>
#include <moveit_visual_tools/moveit_visual_tools.h>
#include <moveit/planning_scene_interface/planning_scene_interface.h>

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    auto const node = std::make_shared<rclcpp::Node>(
        "draw_line_and_circle",
        rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true));

    // Create a ROS logger
    auto const logger = rclcpp::get_logger("draw_line_and_circle");

    // 开启单线程执行器
    rclcpp::executors::SingleThreadedExecutor executor;
    executor.add_node(node);
    auto spinner = std::thread([&executor]()
                               { executor.spin(); });
    using moveit::planning_interface::MoveGroupInterface;
    auto move_group_interface = MoveGroupInterface(node, "panda_arm");

    // 初始化 MoveItVisualTools
    auto moveit_visual_tools = moveit_visual_tools::MoveItVisualTools{
        node, "panda_link0", rviz_visual_tools::RVIZ_MARKER_TOPIC,
        move_group_interface.getRobotModel()};
    moveit_visual_tools.deleteAllMarkers();
    moveit_visual_tools.loadRemoteControl();

    // 为可视化编写闭包
    auto const draw_title = [&moveit_visual_tools](auto text)
    {
        auto const text_pose = []
        {
            auto msg = Eigen::Isometry3d::Identity();
            msg.translation().z() = 1.0;
            return msg;
        }();
        moveit_visual_tools.publishText(text_pose, text, rviz_visual_tools::WHITE,
                                        rviz_visual_tools::XLARGE);
    };

    auto const prompt = [&moveit_visual_tools](auto text)
    {
        moveit_visual_tools.prompt(text);
    };

    // 绘制机械臂末端执行器 ee 的轨迹
    auto const draw_trajectory_tool_path =
        [&moveit_visual_tools,
         jmg = move_group_interface.getRobotModel()->getJointModelGroup(
             "panda_arm")](auto const trajectory)
    {
        moveit_visual_tools.publishTrajectoryLine(trajectory, jmg);
    };

    // 进行路径规划
    // ---
    // 1.获取当前位姿作为起点。
    // ---
    std::vector<geometry_msgs::msg::Pose> waypoints;
    geometry_msgs::msg::Pose start_pose = move_group_interface.getCurrentPose().pose;
    waypoints.push_back(start_pose);

    // 把起点位置赋给终点位置，作为中间变量。
    geometry_msgs::msg::Pose target_pose = start_pose;

    // 2.绘制直线：沿着y轴正半轴移动15cm
    target_pose.position.y += 0.15;
    waypoints.push_back(target_pose);

    // 3. 画圆：在 Y-Z 平面上绘制一个半径为 5 厘米的圆
    double radius = 0.05;
    // 计算圆心。为了保证轨迹平滑，圆心设定在当前点正下方 radius 的位置
    double center_y = target_pose.position.y;
    double center_z = target_pose.position.z - radius;

    // 生成圆上的离散路径点 (以 0.1 弧度为步长)
    for (double th = 0.0; th <= 2.0 * M_PI; th += 0.1)
    {
        target_pose.position.y = center_y + radius * sin(th);
        target_pose.position.z = center_z + radius * cos(th);
        waypoints.push_back(target_pose);
    }

    // -----------------------------------------------------------------
    // 4. 计算笛卡尔路径
    // -----------------------------------------------------------------
    moveit_msgs::msg::RobotTrajectory trajectory;
    const double jump_threshold = 0.0; // 禁用跳跃阈值限制
    const double eef_step = 0.01;      // 末端执行器的步长 (1厘米)

    prompt("单击 RvizVisualToolsGui 窗口的 'Next' 进行笛卡尔路径规划 (直线与圆)");
    draw_title("规划直线与圆");
    moveit_visual_tools.trigger();

    // 计算路径，fraction 表示规划成功的百分比 (0.0 到 1.0)
    double fraction = move_group_interface.computeCartesianPath(waypoints, eef_step, jump_threshold, trajectory);

    RCLCPP_INFO(logger, "笛卡尔路径规划完成 (%.2f%% 成功)", fraction * 100.0);

    // -----------------------------------------------------------------
    // 5. 可视化并执行
    // -----------------------------------------------------------------
    if (fraction > 0.9) // 如果规划成功率高于 90%
    {
        // 绘制计算出的轨迹
        draw_trajectory_tool_path(trajectory);
        moveit_visual_tools.trigger();

        prompt("单击 'Next' 执行该轨迹");
        draw_title("planning...");
        moveit_visual_tools.trigger();

        // 将轨迹转换为 Plan 消息并执行
        moveit::planning_interface::MoveGroupInterface::Plan cartesian_plan;
        cartesian_plan.trajectory_ = trajectory;
        move_group_interface.execute(cartesian_plan);
    }
    else
    {
        draw_title("规划失败!");
        moveit_visual_tools.trigger();
        RCLCPP_ERROR(logger, "笛卡尔路径规划失败或完成度过低!");
    }

    // 关闭 ROS
    rclcpp::shutdown();
    spinner.join();
    return 0;
}
