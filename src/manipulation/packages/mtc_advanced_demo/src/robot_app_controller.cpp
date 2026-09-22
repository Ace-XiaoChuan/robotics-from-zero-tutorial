#include "mtc_advanced_demo/robot_app_controller.hpp"
#include <moveit/task_constructor/task.h>
#include <moveit_msgs/msg/move_it_error_codes.hpp>

static const rclcpp::Logger LOGGER = rclcpp::get_logger("mtc_tutorial_controller");

namespace mtc_advanced_demo
{
    // 构造函数：初始化 node，并将 node 传入 task_builder_
    RobotAppController::RobotAppController(const rclcpp::NodeOptions& options)
        : node_(std::make_shared<rclcpp::Node>("mtc_node", options)),
          task_builder_(node_) 
    {
    }

    rclcpp::node_interfaces::NodeBaseInterface::SharedPtr RobotAppController::getNodeBaseInterface()
    {
        return node_->get_node_base_interface();
    }

    void RobotAppController::run()
    {
        RCLCPP_INFO(LOGGER, "Starting MTC Task Setup...");

        // 1. 设置规划场景
        env_manager_.setupPlanningScene();

        // 2. 构建任务流水线
        auto task = task_builder_.createDemoTask();

        // 3. 初始化任务
        try
        {
            task.init();
        }
        catch (moveit::task_constructor::InitStageException& e)
        {
            RCLCPP_ERROR_STREAM(LOGGER, "Task Initialization Failed: " << e);
            return;
        }

        // 4. 开始规划（参数 5 表示最多保留 5 条备选轨迹）
        if (!task.plan(5))
        {
            RCLCPP_ERROR_STREAM(LOGGER, "Task Planning Failed");
            return;
        }

        RCLCPP_INFO(LOGGER, "Planning succeeded. Publishing solution to RViz...");

        // 5. 发布第一条解决方案以便在 RViz 中可视化
        task.introspection().publishSolution(*task.solutions().front());

        // 6. 执行任务
        auto result = task.execute(*task.solutions().front());
        if (result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS)
        {
            RCLCPP_ERROR_STREAM(LOGGER, "Task Execution Failed with Error Code: " << result.val);
            return;
        }

        RCLCPP_INFO(LOGGER, "Task Executed Successfully!");
    }
} // namespace mtc_advanced_demo