#include <algorithm>
#include "ros2_comm_demo/common.hpp"
#include "geometry_msgs/msg/point_stamped.hpp"
#include "geometry_msgs/msg/twist.hpp"

// A kinematic point in the map plane, not an actuator or rigid-body simulation.
class PoseNode : public rclcpp::Node {
public:
  PoseNode() : Node("pose_node") {
    demo::require_wall_time(*this);
    frame_ = demo::parameter(*this, "frame_id", std::string("map"));
    if (frame_.empty()) { throw std::invalid_argument("frame_id must not be empty"); }
    max_speed_ = demo::positive(*this, "max_speed", 0.5);
    watchdog_ = demo::positive(*this, "command_timeout_s", 0.3);
    const auto seconds = demo::positive(*this, "publish_period_s", 0.05);
    publisher_ = create_publisher<geometry_msgs::msg::PointStamped>("robot_pose", 10);
    command_ = create_subscription<geometry_msgs::msg::Twist>("cmd_vel", 1,
      [this](geometry_msgs::msg::Twist::ConstSharedPtr msg) {
        advance(demo::Clock::now());
        const double speed = std::hypot(msg->linear.x, msg->linear.y);
        if (!std::isfinite(speed)) { vx_ = vy_ = 0.0; return; }
        const double scale = speed > max_speed_ ? max_speed_ / speed : 1.0;
        vx_ = msg->linear.x * scale;
        vy_ = msg->linear.y * scale;
        last_command_ = demo::Clock::now();
      });
    timer_ = create_wall_timer(demo::period(seconds), [this] { tick(); });
  }
private:
  void advance(demo::Clock::time_point now) {
    // Stop integrating at the command expiry, even if this timer is delayed.
    const auto until = std::min(now, last_command_ + demo::period(watchdog_));
    const double dt = std::max(0.0,
      std::chrono::duration<double>(until - last_step_).count());
    x_ += vx_ * dt;
    y_ += vy_ * dt;
    last_step_ = now;
  }
  void tick() {
    advance(demo::Clock::now());
    geometry_msgs::msg::PointStamped pose;
    pose.header.frame_id = frame_;
    pose.header.stamp = get_clock()->now();
    pose.point.x = x_;
    pose.point.y = y_;
    publisher_->publish(pose);
  }
  std::string frame_;
  double max_speed_, watchdog_, x_{0}, y_{0}, vx_{0}, vy_{0};
  demo::Clock::time_point last_step_{demo::Clock::now()}, last_command_{last_step_};
  rclcpp::Publisher<geometry_msgs::msg::PointStamped>::SharedPtr publisher_;
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr command_;
  rclcpp::TimerBase::SharedPtr timer_;
};
int main(int argc, char ** argv) { return demo::run<PoseNode>(argc, argv); }
