#include <chrono>
#include "lesson5_composition/talker.hpp"

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
            RCLCPP_INFO(this->get_logger(), "发布数据：%d(0x%1lX)", msg->data, reinterpret_cast<std::uintptr_t>(msg.get()));
            pub_->publish(std::move(msg));
        };
        timer_ = this->create_wall_timer(1s, callback);
    }

}
