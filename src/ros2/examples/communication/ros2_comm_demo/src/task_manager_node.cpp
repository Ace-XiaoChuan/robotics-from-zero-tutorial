#include <algorithm>
#include <functional>
#include "ros2_comm_demo/common.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "std_msgs/msg/int32.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "robot_interfaces/action/navigation.hpp"
#include "robot_interfaces/srv/get_robot_status.hpp"

class TaskManagerNode : public rclcpp::Node {
  using Navigation = robot_interfaces::action::Navigation;
  using Handle = rclcpp_action::ServerGoalHandle<Navigation>;
  using Status = robot_interfaces::srv::GetRobotStatus;
public:
  TaskManagerNode() : Node("task_manager_node") {
    demo::require_wall_time(*this);
    frame_ = demo::parameter(*this, "frame_id", std::string("map"));
    if (frame_.empty()) { throw std::invalid_argument("frame_id must not be empty"); }
    speed_ = demo::positive(*this, "max_speed", 0.5);
    tolerance_ = demo::positive(*this, "arrival_tolerance", 0.03);
    stale_s_ = demo::positive(*this, "state_timeout_s", 0.8);
    timeout_s_ = demo::positive(*this, "task_timeout_s", 15.0);
    limit_ = demo::positive(*this, "workspace_limit", 5.0);
    min_battery_ = demo::parameter(*this, "min_battery", 20);
    if (min_battery_ < 0 || min_battery_ > 100) {
      throw std::invalid_argument("min_battery must be in [0, 100]");
    }
    velocity_ = create_publisher<geometry_msgs::msg::Twist>("cmd_vel", 1);
    battery_sub_ = create_subscription<std_msgs::msg::Int32>("battery_level", 10,
      [this](std_msgs::msg::Int32::ConstSharedPtr msg) {
        if (msg->data < 0 || msg->data > 100) { return; }
        battery_ = msg->data;
        have_battery_ = true;
        battery_time_ = demo::Clock::now();
      });
    pose_sub_ = create_subscription<geometry_msgs::msg::PointStamped>("robot_pose", 10,
      [this](geometry_msgs::msg::PointStamped::ConstSharedPtr msg) {
        if (msg->header.frame_id != frame_ || !std::isfinite(msg->point.x) ||
          !std::isfinite(msg->point.y) || !std::isfinite(msg->point.z) ||
          std::abs(msg->point.z) > 1e-6 || msg->header.stamp.sec < 0 ||
          msg->header.stamp.nanosec >= 1000000000U) { return; }
        // Require a recent producer timestamp as well as recent reception.
        const double age = (get_clock()->now() - rclcpp::Time(msg->header.stamp)).seconds();
        if (age < -0.1 || age > stale_s_) { return; }
        pose_ = *msg;
        have_pose_ = true;
        pose_time_ = demo::Clock::now();
      });
    status_ = create_service<Status>("get_robot_status",
      [this](Status::Request::SharedPtr, Status::Response::SharedPtr response) {
        response->valid = fresh();
        response->battery_level = have_battery_ ? battery_ : -1;
        response->pose = pose_;
        response->battery_age_s = have_battery_ ? demo::elapsed(battery_time_) : -1.0;
        response->pose_age_s = have_pose_ ? demo::elapsed(pose_time_) : -1.0;
        response->has_task = busy_;
        response->message = fresh() ? "state available" : "state missing or stale";
      });
    server_ = rclcpp_action::create_server<Navigation>(this, "navigation",
      [this](const rclcpp_action::GoalUUID &, std::shared_ptr<const Navigation::Goal> goal) {
        if (busy_ || !fresh() || battery_ < min_battery_ ||
          !std::isfinite(goal->target_x) || !std::isfinite(goal->target_y) ||
          std::abs(goal->target_x) > limit_ || std::abs(goal->target_y) > limit_) {
          RCLCPP_WARN(get_logger(), "Rejected goal: busy, invalid target or unavailable state");
          return rclcpp_action::GoalResponse::REJECT;
        }
        // Reserve the slot before the accepted callback can be dispatched.
        busy_ = true;
        return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
      },
      [](std::shared_ptr<Handle>) { return rclcpp_action::CancelResponse::ACCEPT; },
      [this](std::shared_ptr<Handle> handle) {
        active_ = handle;
        started_ = demo::Clock::now();
        RCLCPP_INFO(get_logger(), "Accepted goal (%.2f, %.2f)",
          handle->get_goal()->target_x, handle->get_goal()->target_y);
      });
    timer_ = create_wall_timer(std::chrono::milliseconds(50), [this] { tick(); });
  }
private:
  bool fresh() {
    // The producer stamp was checked on receipt. Use a monotonic clock here so
    // an NTP/system-clock adjustment cannot invalidate an otherwise live stream.
    return have_pose_ && have_battery_ && demo::elapsed(pose_time_) <= stale_s_ &&
      demo::elapsed(battery_time_) <= stale_s_;
  }
  double distance() const {
    return std::hypot(active_->get_goal()->target_x - pose_.point.x,
      active_->get_goal()->target_y - pose_.point.y);
  }
  void finish(const std::string & reason, bool success = false, bool canceled = false) {
    velocity_->publish(geometry_msgs::msg::Twist{});
    auto result = std::make_shared<Navigation::Result>();
    result->success = success;
    result->message = reason;
    result->final_distance = distance();
    if (canceled) { active_->canceled(result); }
    else if (success) { active_->succeed(result); }
    else { active_->abort(result); }
    RCLCPP_INFO(get_logger(), "Finished: %s, distance=%.4f", reason.c_str(), result->final_distance);
    active_.reset();
    busy_ = false;
  }
  void tick() {
    if (!active_) { return; }
    if (active_->is_canceling()) { finish("canceled", false, true); return; }
    if (!fresh()) { finish("state missing or stale"); return; }
    if (battery_ < min_battery_) { finish("low battery"); return; }
    if (demo::elapsed(started_) > timeout_s_) { finish("task timeout"); return; }
    const double remaining = distance();
    if (remaining <= tolerance_) { finish("arrived", true); return; }
    geometry_msgs::msg::Twist command;
    // Proportional planar velocity, limited in norm; no orientation or collision planning.
    const double factor = std::min(2.0, speed_ / remaining);
    command.linear.x = factor * (active_->get_goal()->target_x - pose_.point.x);
    command.linear.y = factor * (active_->get_goal()->target_y - pose_.point.y);
    velocity_->publish(command);
    auto feedback = std::make_shared<Navigation::Feedback>();
    feedback->current_x = pose_.point.x;
    feedback->current_y = pose_.point.y;
    feedback->distance_remaining = remaining;
    active_->publish_feedback(feedback);
  }
  // All callbacks run in the single-threaded executor; no detached threads or locks.
  std::string frame_;
  double speed_, tolerance_, stale_s_, timeout_s_, limit_;
  int min_battery_, battery_{-1};
  bool have_battery_{false}, have_pose_{false}, busy_{false};
  geometry_msgs::msg::PointStamped pose_;
  demo::Clock::time_point battery_time_, pose_time_, started_;
  std::shared_ptr<Handle> active_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr velocity_;
  rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr battery_sub_;
  rclcpp::Subscription<geometry_msgs::msg::PointStamped>::SharedPtr pose_sub_;
  rclcpp::Service<Status>::SharedPtr status_;
  rclcpp_action::Server<Navigation>::SharedPtr server_;
  rclcpp::TimerBase::SharedPtr timer_;
};
int main(int argc, char ** argv) { return demo::run<TaskManagerNode>(argc, argv); }
