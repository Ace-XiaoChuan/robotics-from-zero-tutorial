#include <memory>

#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/int32.hpp"
#include "rclcpp_action/rclcpp_action.hpp"

#include "robot_interfaces/srv/get_robot_status.hpp"
#include "robot_interfaces/action/navigation.hpp"

using namespace std::chrono_literals;

class CommandNode : public rclcpp::Node
{
public:
    using Navigation = robot_interfaces::action::Navigation;
    using GoalHandleNavigation = rclcpp_action::ClientGoalHandle<Navigation>;

    CommandNode() : Node("command")
    {
        subscription_ = this->create_subscription<std_msgs::msg::Int32>(
            "battery_level", 10,
            [this](std_msgs::msg::Int32::SharedPtr msg)
            { current_battery_ = msg->data; });

        service_client_ = this->create_client<robot_interfaces::srv::GetRobotStatus>(
            "get_robot_status");
        service_timer_ = this->create_wall_timer(
            3s, [this]()
            { send_request(); });

        action_client_ = rclcpp_action::create_client<Navigation>(
            this, "Navigation");

        action_timer_ = this->create_wall_timer(
            2s, [this]()
            { send_goal(); });
    }

private:
    int current_battery_ = 0;
    bool goal_sent_ = false;

    rclcpp::Subscription<std_msgs::msg::Int32>::SharedPtr subscription_;
    rclcpp::Client<robot_interfaces::srv::GetRobotStatus>::SharedPtr service_client_;
    rclcpp::TimerBase::SharedPtr service_timer_;

    rclcpp_action::Client<Navigation>::SharedPtr action_client_; 
    rclcpp::TimerBase::SharedPtr action_timer_;

    void send_request()
    {
        if (!service_client_->wait_for_service(1s))
        {
            RCLCPP_WARN(this->get_logger(), "等待服务上线...");
            return;
        }
        auto request = std::make_shared<robot_interfaces::srv::GetRobotStatus::Request>();
        service_client_->async_send_request(request,
                                            [this](rclcpp::Client<robot_interfaces::srv::GetRobotStatus>::SharedFuture future)
                                            {
                                                auto response = future.get();
                                                RCLCPP_INFO(this->get_logger(),
                                                            "【状态】电量:%d 位置:(%.1f,%.1f,%.1f) 任务:%s",
                                                            response->battery_level,
                                                            response->x, response->y, response->z,
                                                            response->has_task ? "是" : "否");
                                            });
    }

    void send_goal()
    {
        action_timer_->cancel();

        if (goal_sent_)
            return;

        if (!action_client_->wait_for_action_server(3s))
        {
            RCLCPP_ERROR(this->get_logger(), "动作服务器不在线！");
            return;
        }

        auto goal_msg = Navigation::Goal();
        goal_msg.target_x = 5.0;
        goal_msg.target_y = 3.0;
        RCLCPP_INFO(this->get_logger(), "发送导航目标: (%.1f, %.1f)",
                    goal_msg.target_x, goal_msg.target_y);

        auto send_goal_options =
            rclcpp_action::Client<Navigation>::SendGoalOptions();

        send_goal_options.goal_response_callback =
            [this](const GoalHandleNavigation::SharedPtr &goal_handle)
        {
            goal_response_callback(goal_handle);
        };

        send_goal_options.feedback_callback =
            [this](GoalHandleNavigation::SharedPtr,
                   const std::shared_ptr<const Navigation::Feedback> feedback)
        {
            feedback_callback(feedback);
        };

        send_goal_options.result_callback =
            [this](const GoalHandleNavigation::WrappedResult &result)
        {
            result_callback(result);
        };

        action_client_->async_send_goal(goal_msg, send_goal_options);
        goal_sent_ = true;
    }

    void goal_response_callback(const GoalHandleNavigation::SharedPtr &goal_handle)
    {
        if (!goal_handle)
        {
            RCLCPP_ERROR(this->get_logger(), "❌ 目标被服务端拒绝！");
        }
        else
        {
            RCLCPP_INFO(this->get_logger(), "✅ 目标被接受，等待执行...");
        }
    }

    void feedback_callback(const std::shared_ptr<const Navigation::Feedback> feedback)
    {
        RCLCPP_INFO(this->get_logger(),
                    "📡 反馈 -> 当前位置: (%.2f, %.2f), 剩余距离: %.2f",
                    feedback->current_x,
                    feedback->current_y,
                    feedback->distance_remaining);
    }

    void result_callback(const GoalHandleNavigation::WrappedResult &result)
    {
        switch (result.code)
        {
        case rclcpp_action::ResultCode::SUCCEEDED:
            RCLCPP_INFO(this->get_logger(), "🎉 导航成功！消息: %s",
                        result.result->message.c_str());
            break;
        case rclcpp_action::ResultCode::ABORTED:
            RCLCPP_ERROR(this->get_logger(), "💥 导航被中止！消息: %s",
                         result.result->message.c_str());
            break;
        case rclcpp_action::ResultCode::CANCELED:
            RCLCPP_WARN(this->get_logger(), "⚠️  导航被取消！消息: %s",
                        result.result->message.c_str());
            break;
        default:
            RCLCPP_ERROR(this->get_logger(), "未知结果");
            break;
        }
    }
};

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<CommandNode>());
    rclcpp::shutdown();
    return 0;
}
