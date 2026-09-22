#include "lesson2_composition/listener.hpp"
#include "rclcpp_components/register_node_macro.hpp"

namespace learn_compose
{
    Listener::Listener(const rclcpp::NodeOptions &options) : Node("listener", options)
    {
        sub_ = this->create_subscription<std_msgs::msg::Int32>("count", 10, [&](std_msgs::msg::Int32::UniquePtr msg)
                                                               { RCLCPP_INFO(this->get_logger(), "收到数据：%d (message=%p)", msg->data, static_cast<void *>(msg.get())); });
    }

}  // namespace learn_compose

RCLCPP_COMPONENTS_REGISTER_NODE(learn_compose::Listener)
