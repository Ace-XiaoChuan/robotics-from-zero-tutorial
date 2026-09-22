#include <rclcpp/rclcpp.hpp>
#include <string>
#include <moveit/task_constructor/task.h>
#include <moveit/task_constructor/solvers.h>


namespace mtc = moveit::task_constructor;
namespace mtc_advanced_demo
{
    class TaskBuilder
    {
    public:
        TaskBuilder(rclcpp::Node::SharedPtr node);
        ~TaskBuilder() = default;
        mtc::Task createDemoTask();

    private:
        rclcpp::Node::SharedPtr node_;
        std::string arm_group_name_;
        std::string hand_group_name_;
        std::string hand_frame_;

        std::shared_ptr<mtc::solvers::PipelinePlanner> sampling_planner_;
        std::shared_ptr<mtc::solvers::JointInterpolationPlanner> interpolation_planner_;
        std::shared_ptr<mtc::solvers::CartesianPath> cartesian_planner_;
        void initSolvers();
    };
} // namespace mtc_advanced_demo
