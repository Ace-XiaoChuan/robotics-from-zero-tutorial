#include <chrono>

#include "lesson5_composition/listener.hpp"

namespace learn_compose
{
    using namespace std::chrono_literals;

    Listener::Listener(const rclcpp::NodeOptions &options) : Node("listener", options)
    {
        sub_ = this->create_subscription<std_msgs::msg::Int32>("count", 10, [&](const std_msgs::msg::Int32::UniquePtr msg)
                                                               { RCLCPP_INFO(this->get_logger(), "收到数据：%d(0x%1lX)", msg->data, reinterpret_cast<std::uintptr_t>(msg.get())); });
    };

}
