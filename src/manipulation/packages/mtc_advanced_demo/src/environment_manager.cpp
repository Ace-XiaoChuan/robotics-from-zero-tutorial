#include <vector>

#include <moveit_msgs/msg/collision_object.hpp>
#include <shape_msgs/msg/solid_primitive.hpp>

#include "mtc_advanced_demo/environment_manager.hpp"

namespace mtc_advanced_demo
{
    // 1. 实现 setupPlanningScene
    void EnvironmentManager::setupPlanningScene()
    {
        geometry_msgs::msg::Pose pose;
        pose.position.x = 0.5;
        pose.position.y = -0.25;
        pose.orientation.w = 1.0;
        // 参数：名字, 姿态, 高度0.1, 半径0.02
        addCylinder("object", pose, 0.1, 0.02);
    }

    // 2. 实现 addCylinder
    void EnvironmentManager::addCylinder(const std::string &id, const geometry_msgs::msg::Pose &pose, double height, double radius)
    {
        moveit_msgs::msg::CollisionObject object;
        object.id = id;
        object.header.frame_id = "world"; // 假设在 world 坐标系下

        // 定义物体的形状：圆柱体
        object.primitives.resize(1);
        object.primitives[0].type = shape_msgs::msg::SolidPrimitive::CYLINDER;
        object.primitives[0].dimensions = {height, radius};

        // 设置位姿
        object.pose = pose;

        psi_.applyCollisionObject(object);
    }

    // 3. 实现 removeObject
    void EnvironmentManager::removeObject(const std::string &id)
    {
        // PlanningSceneInterface 要求传入一个包含物体 ID 的 vector 来进行批量删除
        std::vector<std::string> object_ids;
        object_ids.push_back(id);

        psi_.removeCollisionObjects(object_ids);
    }
}
