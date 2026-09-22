#include <rclcpp/rclcpp.hpp>
#include <string>
#include <geometry_msgs/msg/pose.hpp>
#include <moveit/planning_scene_interface/planning_scene_interface.h>

namespace mtc_advanced_demo
{
    class EnvironmentManager
    {
    public:
        EnvironmentManager() = default;
        ~EnvironmentManager() = default; // 生成析构函数的默认实现，不写{}意图更明显。
        void setupPlanningScene();
        void addCylinder(const std::string &id, const geometry_msgs::msg::Pose &pose, double height, double radius);
        void removeObject(const std::string &id);

    private:
        moveit::planning_interface::PlanningSceneInterface psi_;
    };
} // namespace mtc_advanced_demo