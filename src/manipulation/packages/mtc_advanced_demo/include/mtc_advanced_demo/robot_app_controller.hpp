#pragma once

#include <rclcpp/rclcpp.hpp>
#include "mtc_advanced_demo/environment_manager.hpp"
#include "mtc_advanced_demo/task_builder.hpp"

namespace mtc_advanced_demo
{
    class RobotAppController
    {
    public:
        RobotAppController(const rclcpp::NodeOptions &options);
        ~RobotAppController() = default;

        // 获取节点底层接口，用于 Executor 挂载
        rclcpp::node_interfaces::NodeBaseInterface::SharedPtr getNodeBaseInterface();

        // 核心调度函数
        void run();

    private:
        rclcpp::Node::SharedPtr node_;
        EnvironmentManager env_manager_;
        TaskBuilder task_builder_;
    };
} // namespace mtc_advanced_demo