#include <chrono>

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/point_stamped.hpp"

using namespace std::chrono_literals;

class PoseNode : public rclcpp::Node
{
public:
    PoseNode() : Node("pose_node")
    {
        publisher_ = this->create_publisher<geometry_msgs::msg::PointStamped>("robot_pose", 10);
        timer_ = this->create_wall_timer(1000ms, [this]()
                                         { timer_callback(); });
    }

private:
    double current_x_ = 0.0;
    rclcpp::Publisher<geometry_msgs::msg::PointStamped>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;

    void timer_callback()
    {
        auto point_stamp = geometry_msgs::msg::PointStamped();
        point_stamp.header.stamp = this->get_clock()->now();

        point_stamp.header.frame_id = "map";
        current_x_ += 0.1;
        point_stamp.point.x = current_x_;
        point_stamp.point.y = 0.0;
        point_stamp.point.z = 0.0;
        RCLCPP_INFO(this->get_logger(), "发布位置:xyz坐标分别为: % .1f, % .1f, % .1f", point_stamp.point.x, point_stamp.point.y, point_stamp.point.z);
        publisher_->publish(point_stamp);
    }
};

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<PoseNode>());
    rclcpp::shutdown();
    return 0;
}
