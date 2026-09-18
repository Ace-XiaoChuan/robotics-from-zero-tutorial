#include <chrono>

#include "std_msgs/msg/int32.hpp"
#include "rclcpp/rclcpp.hpp"

using namespace std::chrono_literals;

class BatteryNode : public rclcpp::Node
{
public:
    BatteryNode() : Node("battery_node")
    {
        publisher_ = this->create_publisher<std_msgs::msg::Int32>("battery_level", 10);
        timer_ = this->create_wall_timer(1000ms, [this]()
                                         { timer_callback(); });
    }

private:
    int battery_level = 100;
    rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;

    void timer_callback()
    {
        auto message = std_msgs::msg::Int32();
        if (battery_level > 0)
        {
            battery_level--;
        }
        message.data = battery_level;
        RCLCPP_INFO(this->get_logger(), "Publishing battery level: %d%%", message.data);
        publisher_->publish(message);
    }
};

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<BatteryNode>());
    rclcpp::shutdown();
    return 0;
}
