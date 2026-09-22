#include <future>
#include "ros2_comm_demo/common.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "robot_interfaces/action/navigation.hpp"
#include "robot_interfaces/srv/get_robot_status.hpp"

class CommandNode : public rclcpp::Node {
  using Navigation = robot_interfaces::action::Navigation;
  using Handle = rclcpp_action::ClientGoalHandle<Navigation>;
  using Status = robot_interfaces::srv::GetRobotStatus;
public:
  CommandNode() : Node("command") {
    demo::require_wall_time(*this);
    target_x_ = demo::parameter(*this, "target_x", 1.0);
    target_y_ = demo::parameter(*this, "target_y", 0.5);
    if (!std::isfinite(target_x_) || !std::isfinite(target_y_)) {
      throw std::invalid_argument("target must be finite");
    }
    startup_s_ = demo::positive(*this, "startup_timeout_s", 30.0);
    result_s_ = demo::positive(*this, "result_timeout_s", 20.0);
    client_ = create_client<Status>("get_robot_status");
    action_ = rclcpp_action::create_client<Navigation>(this, "navigation");
    timer_ = create_wall_timer(std::chrono::milliseconds(200), [this] { tick(); });
  }
private:
  void tick() {
    if (sent_) {
      if (demo::elapsed(sent_at_) > result_s_) {
        if (handle_) { action_->async_cancel_goal(handle_); }
        RCLCPP_ERROR(get_logger(), "Result timeout: outcome unconfirmed; no automatic resend");
        timer_->cancel();
      }
      return;
    }
    if (demo::elapsed(started_) > startup_s_) {
      if (pending_) { client_->remove_pending_request(request_id_); }
      RCLCPP_ERROR(get_logger(), "Startup timeout: no valid state/action server");
      timer_->cancel();
      return;
    }
    if (pending_) {
      if (demo::elapsed(requested_) > 2.0) {
        client_->remove_pending_request(request_id_);
        pending_ = false;
      }
      return;
    }
    if (!client_->service_is_ready() || !action_->action_server_is_ready()) { return; }
    pending_ = true;
    requested_ = demo::Clock::now();
    const auto request = client_->async_send_request(std::make_shared<Status::Request>(),
      [this](rclcpp::Client<Status>::SharedFuture future) {
        pending_ = false;
        const auto state = future.get();
        RCLCPP_INFO(get_logger(), "Status valid=%d battery=%d busy=%d",
          state->valid, state->battery_level, state->has_task);
        if (state->valid && !state->has_task && !sent_) { send_goal(); }
      });
    request_id_ = request.request_id;
  }
  void send_goal() {
    Navigation::Goal goal;
    goal.target_x = target_x_;
    goal.target_y = target_y_;
    rclcpp_action::Client<Navigation>::SendGoalOptions options;
    options.goal_response_callback = [this](Handle::SharedPtr handle) {
      RCLCPP_INFO(get_logger(), "Goal %s", handle ? "accepted" : "rejected");
      handle_ = handle;
      if (!handle) { timer_->cancel(); }
      // Do not silently retry a rejected/uncertain movement request.
    };
    options.feedback_callback = [this](Handle::SharedPtr,
      const std::shared_ptr<const Navigation::Feedback> feedback) {
      RCLCPP_INFO_THROTTLE(get_logger(), *get_clock(), 1000,
        "Distance remaining: %.3f m", feedback->distance_remaining);
    };
    options.result_callback = [this](const Handle::WrappedResult & result) {
      timer_->cancel();
      RCLCPP_INFO(get_logger(), "Result code=%d success=%d message=%s distance=%.4f",
        static_cast<int>(result.code), result.result->success,
        result.result->message.c_str(), result.result->final_distance);
    };
    sent_ = true;
    sent_at_ = demo::Clock::now();
    action_->async_send_goal(goal, options);
  }
  double target_x_, target_y_, startup_s_, result_s_;
  bool sent_{false}, pending_{false};
  int64_t request_id_{0};
  demo::Clock::time_point started_{demo::Clock::now()}, requested_, sent_at_;
  Handle::SharedPtr handle_;
  rclcpp::Client<Status>::SharedPtr client_;
  rclcpp_action::Client<Navigation>::SharedPtr action_;
  rclcpp::TimerBase::SharedPtr timer_;
};
int main(int argc, char ** argv) { return demo::run<CommandNode>(argc, argv); }
