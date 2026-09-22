#ifndef LESSON2_COMPOSITION__LISTENER_HPP_
#define LESSON2_COMPOSITION__LISTENER_HPP_
#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/int32.hpp"

namespace learn_compose
{
    class Listener : public rclcpp::Node
    {
    public:
        explicit Listener(const rclcpp::NodeOptions &options);

    private:
        rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr sub_;
    };

}  // namespace learn_compose

#endif  // LESSON2_COMPOSITION__LISTENER_HPP_
