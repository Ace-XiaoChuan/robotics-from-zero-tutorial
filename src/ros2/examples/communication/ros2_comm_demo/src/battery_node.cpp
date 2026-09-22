#include <algorithm>
#include "ros2_comm_demo/common.hpp"
#include "std_msgs/msg/int32.hpp"

class BatteryNode : public rclcpp::Node {
public:
  BatteryNode() : Node("battery_node") {
    demo::require_wall_time(*this);
    level_ = demo::parameter(*this, "initial_level", 100);
    drain_ = demo::parameter(*this, "drain_per_tick", 0);
    if (level_ < 0 || level_ > 100 || drain_ < 0 || drain_ > 100) {
      throw std::invalid_argument("battery parameters must be in [0, 100]");
    }
    const auto seconds = demo::positive(*this, "publish_period_s", 0.2);
    publisher_ = create_publisher<std_msgs::msg::Int32>("battery_level", 10);
    timer_ = create_wall_timer(demo::period(seconds), [this] {
      std_msgs::msg::Int32 message;
      message.data = level_;
      publisher_->publish(message);
      level_ = std::max(0, level_ - drain_);
    });
  }
private:
  int level_, drain_;
  rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
};
int main(int argc, char ** argv) { return demo::run<BatteryNode>(argc, argv); }
