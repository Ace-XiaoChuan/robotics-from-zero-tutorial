#include <chrono>
#include <memory>

#include "lesson2_composition/talker.hpp"
#include "rclcpp_components/register_node_macro.hpp"

namespace learn_compose
{
    using namespace std::chrono_literals;
    Talker::Talker(const rclcpp::NodeOptions &options) : Node("talker", options)
    {
        pub_ = this->create_publisher<std_msgs::msg::Int32>("count", 10);
        auto callback = [&]() -> void
        {
            std::unique_ptr<std_msgs::msg::Int32> msg = std::make_unique<std_msgs::msg::Int32>();
            msg->data = count_++;
            RCLCPP_INFO(this->get_logger(), "发布数据：%d (message=%p)", msg->data, static_cast<void *>(msg.get()));
            pub_->publish(std::move(msg));
        };
        timer_ = this->create_wall_timer(1s, callback);
    }

}  // namespace learn_compose

RCLCPP_COMPONENTS_REGISTER_NODE(learn_compose::Talker)
