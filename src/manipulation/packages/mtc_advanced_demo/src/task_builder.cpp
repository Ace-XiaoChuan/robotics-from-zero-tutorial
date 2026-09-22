#include <moveit/task_constructor/stages.h>

#include "mtc_advanced_demo/task_builder.hpp"
namespace mtc = moveit::task_constructor;
namespace mtc_advanced_demo
{
    // 1. 构造函数：初始化基础参数并调用求解器初始化
    TaskBuilder::TaskBuilder(rclcpp::Node::SharedPtr node) : node_(node), arm_group_name_("panda_arm"), hand_group_name_("hand"),
                                                             hand_frame_("panda_hand")
    {
        initSolvers();
    }

    // 2. 初始化所有规划求解器
    void TaskBuilder::initSolvers()
    {
        // 采样规划器（用于无碰撞的全局路径规划，如 MoveGroup）
        sampling_planner_ = std::make_shared<mtc::solvers::PipelinePlanner>(node_);

        // 关节插值规划器（用于简单的状态切换，如张开/闭合夹爪）

        interpolation_planner_ = std::make_shared<mtc::solvers::JointInterpolationPlanner>();
        // 笛卡尔直线规划器（用于靠近和撤离物体的直线运动）
        cartesian_planner_ = std::make_shared<mtc::solvers::CartesianPath>();
        cartesian_planner_->setMaxVelocityScalingFactor(1.0);
        cartesian_planner_->setMaxAccelerationScalingFactor(1.0);
        cartesian_planner_->setStepSize(.01);
    }

    // 3. 组装 MTC 任务流水线
    mtc::Task TaskBuilder::createDemoTask()
    {
        mtc::Task task;
        task.stages()->setName("demo task");
        task.loadRobotModel(node_);

        // 统一设置任务级属性，后续的 Stage 会自动继承这些属性
        task.setProperty("group", arm_group_name_);
        task.setProperty("eef", hand_group_name_);
        task.setProperty("ik_frame", hand_frame_);

        // ---- 阶段 1: 获取当前状态 ----
        auto stage_state_current = std::make_unique<mtc::stages::CurrentState>("current");
        task.add(std::move(stage_state_current));

        // ---- 阶段 2: 张开机械爪 ----
        // 注意：这里传入了我们在 initSolvers 中初始化的 interpolation_planner_
        auto stage_open_hand = std::make_unique<mtc::stages::MoveTo>("open hand", interpolation_planner_);
        stage_open_hand->setGroup(hand_group_name_);
        stage_open_hand->setGoal("open"); // 对应 SRDF 中定义的 named pose
        task.add(std::move(stage_open_hand));

        return task;
    }

}