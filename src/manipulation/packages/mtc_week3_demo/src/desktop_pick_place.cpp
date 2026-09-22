#include <atomic>
#include <cmath>
#include <thread>

#include <moveit/planning_scene/planning_scene.h>
#include <moveit/planning_scene_interface/planning_scene_interface.h>
#include <moveit/task_constructor/solvers.h>
#include <moveit/task_constructor/stages.h>
#include <moveit/task_constructor/task.h>
#include <rclcpp/rclcpp.hpp>
#if __has_include(<tf2_geometry_msgs/tf2_geometry_msgs.hpp>)
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#else
#include <tf2_geometry_msgs/tf2_geometry_msgs.h>
#endif
#if __has_include(<tf2_eigen/tf2_eigen.hpp>)
#include <tf2_eigen/tf2_eigen.hpp>
#else
#include <tf2_eigen/tf2_eigen.h>
#endif

static const rclcpp::Logger LOGGER = rclcpp::get_logger("desktop_pick_place");
namespace mtc = moveit::task_constructor;

class DesktopPickPlace {
public:
  DesktopPickPlace(const rclcpp::NodeOptions &options);
  rclcpp::node_interfaces::NodeBaseInterface::SharedPtr getNodeBaseInterface();
  void doTask();
  void setupPlanningScene();

private:
  mtc::Task createTask();
  mtc::Task task_;
  rclcpp::Node::SharedPtr node_;
};

// ---具体实现---

DesktopPickPlace::DesktopPickPlace(const rclcpp::NodeOptions &options)
    : node_{std::make_shared<rclcpp::Node>("desktop_pick_place", options)} {}
rclcpp::node_interfaces::NodeBaseInterface::SharedPtr
DesktopPickPlace::getNodeBaseInterface() {
  return node_->get_node_base_interface();
}

void DesktopPickPlace::setupPlanningScene() {
  std::vector<moveit_msgs::msg::CollisionObject> collision_objects;

  // ------
  // table
  // ------
  moveit_msgs::msg::CollisionObject table;
  table.id = "table";
  table.header.frame_id = "world";
  table.primitives.resize(1);
  table.primitives[0].type = shape_msgs::msg::SolidPrimitive::BOX;
  table.primitives[0].dimensions = {0.8, 0.5, 0.04};

  geometry_msgs::msg::Pose table_pose;
  table_pose.position.x = 0.6;
  table_pose.position.y = 0.0;
  table_pose.position.z = 0.20;
  table_pose.orientation.w = 1.0;
  table.pose = table_pose;
  collision_objects.push_back(table);

  // -------------------------
  // 2. Object box
  // -------------------------
  moveit_msgs::msg::CollisionObject object;
  const std::string object_id = "box";
  object.id = object_id;
  object.header.frame_id = "world";

  object.primitives.resize(1);
  object.primitives[0].type = shape_msgs::msg::SolidPrimitive::BOX;
  object.primitives[0].dimensions = {0.04, 0.04, 0.08}; // x, y, z

  geometry_msgs::msg::Pose object_pose;
  object_pose.position.x = 0.6;
  object_pose.position.y = -0.20;
  object_pose.position.z = 0.26;
  object_pose.orientation.w = 1.0;

  object.pose = object_pose;
  collision_objects.push_back(object);

  // -------------------------
  // 3. Target area
  // -------------------------
  moveit_msgs::msg::CollisionObject target;
  target.id = "target_area";
  target.header.frame_id = "world";

  target.primitives.resize(1);
  target.primitives[0].type = shape_msgs::msg::SolidPrimitive::BOX;
  target.primitives[0].dimensions = {0.12, 0.12, 0.005}; // x, y, z

  geometry_msgs::msg::Pose target_pose;
  target_pose.position.x = 0.60;
  target_pose.position.y = 0.20;
  target_pose.position.z = 0.2225;
  target_pose.orientation.w = 1.0;

  target.pose = target_pose;
  // collision_objects.push_back(target);

  // 同步到机器人的大脑（规划场景）
  moveit::planning_interface::PlanningSceneInterface psi;
  psi.applyCollisionObjects(collision_objects);

  RCLCPP_INFO(LOGGER, "[W3][scene] Added table and box");
  RCLCPP_INFO(LOGGER,
              "[W3][scene] target_area is not added as collision object");
}

void DesktopPickPlace::doTask() {
  task_ = createTask();
  try {
    task_.init();
  } catch (mtc::InitStageException &e) {
    RCLCPP_ERROR_STREAM(LOGGER, e);
    return;
  }
  if (!task_.plan(5)) {
    RCLCPP_ERROR_STREAM(LOGGER, "Task planning failed");
    return;
  }
  task_.introspection().publishSolution(*task_.solutions().front());
  auto result = task_.execute(*task_.solutions().front());
  if (result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS) {
    RCLCPP_ERROR_STREAM(LOGGER, "Task execution failed");
    return;
  }
  RCLCPP_INFO(LOGGER, "Task execution succeeded");
  return;
}

// cpp得注意下作用域DesktopPickPlace，否则类外函数会认为是全局函数
mtc::Task DesktopPickPlace::createTask() {
  mtc::Task task;
  task.stages()->setName("desktop_pick_place");
  task.loadRobotModel(node_);
  const auto &arm_group_name = "panda_arm";
  const auto &hand_group_name = "hand";
  const auto &hand_frame = "panda_hand";
  const auto &object_id = "box";
  task.setProperty("group", "panda_arm");
  task.setProperty("eef", "hand");
  task.setProperty("ik_frame", "panda_hand");

  auto sampling_planner =
      std::make_shared<mtc::solvers::PipelinePlanner>(node_);
  auto interpolation_planner =
      std::make_shared<mtc::solvers::JointInterpolationPlanner>();
  auto cartesian_planner = std::make_shared<mtc::solvers::CartesianPath>();
  cartesian_planner->setMaxVelocityScalingFactor(1.0);
  cartesian_planner->setMaxAccelerationScalingFactor(1.0);
  cartesian_planner->setStepSize(.01);

  mtc::Stage *current_state_ptr = nullptr;
  // ---
  // 开始定义stages
  // ---
  // 0.current
  auto stage_state_current =
      std::make_unique<mtc::stages::CurrentState>("current");
  current_state_ptr = stage_state_current.get();
  task.add(std::move(stage_state_current));

  // 1.open hand
  auto stage_open_hand =
      std::make_unique<mtc::stages::MoveTo>("open hand", interpolation_planner);
  stage_open_hand->setGroup(hand_group_name);
  stage_open_hand->setGoal("open");
  task.add(std::move(stage_open_hand));

  // 2.move to pick
  auto stage_move_to_pick = std::make_unique<mtc::stages::Connect>(
      "move to pick", mtc::stages::Connect::GroupPlannerVector{
                          {arm_group_name, sampling_planner}});
  stage_move_to_pick->setTimeout(5.0);
  stage_move_to_pick->properties().configureInitFrom(mtc::Stage::PARENT);
  task.add(std::move(stage_move_to_pick));

  mtc::Stage *attach_object_stage = nullptr; //接触物体指针

  {
    // 3.pick object
    auto grasp = std::make_unique<mtc::SerialContainer>("pick object");
    task.properties().exposeTo(grasp->properties(),
                               {"eef", "group", "ik_frame"});
    grasp->properties().configureInitFrom(mtc::Stage::PARENT,
                                          {"eef", "group", "ik_frame"});
    { // 3.1 approach object
      auto stage = std::make_unique<mtc::stages::MoveRelative>(
          "approach object", cartesian_planner);
      stage->properties().set("marker_ns", "approach_object");
      stage->properties().set("link", hand_frame);
      stage->properties().configureInitFrom(mtc::Stage::PARENT, {"group"});
      stage->setMinMaxDistance(0.08, 0.14);
      geometry_msgs::msg::Vector3Stamped vec;
      vec.header.frame_id = hand_frame;
      vec.vector.z = 1.0;
      stage->setDirection(vec);
      grasp->insert(std::move(stage));
    }
    {
      // 3.2 generate grasp pose (侧抓)
      RCLCPP_INFO(LOGGER,
                  "[W3][generate grasp pose] object=%s angle_delta=%.3f",
                  object_id, M_PI / 12.0);

      auto stage = std::make_unique<mtc::stages::GenerateGraspPose>(
          "generate grasp pose");

      stage->properties().configureInitFrom(mtc::Stage::PARENT);
      stage->properties().set("marker_ns", "grasp_pose");

      stage->setPreGraspPose("open");
      stage->setObject(object_id);
      stage->setAngleDelta(M_PI / 12); //每隔 15 度采样一个抓取角度
      stage->setMonitoredStage(current_state_ptr);

      Eigen::Isometry3d grasp_frame_transform = Eigen::Isometry3d::Identity();
      Eigen::Quaterniond q =
          Eigen::AngleAxisd(M_PI / 2, Eigen::Vector3d::UnitX()) *
          Eigen::AngleAxisd(M_PI / 2, Eigen::Vector3d::UnitY()) *
          Eigen::AngleAxisd(M_PI / 2, Eigen::Vector3d::UnitZ());
      grasp_frame_transform.linear() = q.matrix();
      grasp_frame_transform.translation().z() = 0.1;

      auto wrapper = std::make_unique<mtc::stages::ComputeIK>("grasp pose IK",
                                                              std::move(stage));
      wrapper->setMaxIKSolutions(8);
      wrapper->setMinSolutionDistance(1.0);
      wrapper->setIKFrame(grasp_frame_transform, hand_frame);
      wrapper->properties().configureInitFrom(mtc::Stage::PARENT,
                                              {"eef", "group"});
      wrapper->properties().configureInitFrom(mtc::Stage::INTERFACE,
                                              {"target_pose"});
      grasp->insert(std::move(wrapper));
    }
    {
      // 3.3 allow collision
      RCLCPP_INFO(
          LOGGER,
          "[W3][allow collision] allow the collision of hand and object");
      auto stage = std::make_unique<mtc::stages::ModifyPlanningScene>(
          "allow collision (hand,object)");
      stage->allowCollisions(object_id,
                             task.getRobotModel()
                                 ->getJointModelGroup(hand_group_name)
                                 ->getLinkModelNamesWithCollisionGeometry(),
                             true);
      grasp->insert(std::move(stage));
    }
    {
      // 3.4 close hand
      RCLCPP_INFO(LOGGER, "[W3][close hand] close hand");
      auto stage = std::make_unique<mtc::stages::MoveTo>("close hand",
                                                         interpolation_planner);
      stage->setGroup(hand_group_name);
      stage->setGoal("close");
      grasp->insert(std::move(stage));
    }
    {
      // 3.5 attach object
      RCLCPP_INFO(LOGGER, "[W3][attach object] attach the object");
      auto stage =
          std::make_unique<mtc::stages::ModifyPlanningScene>("attach object");
      stage->attachObject(object_id, hand_frame);
      attach_object_stage = stage.get();
      grasp->insert(std::move(stage));
    }
    {
      RCLCPP_INFO(LOGGER,
                  "[W3][collision] allow contact between box and table");
      auto stage = std::make_unique<mtc::stages::ModifyPlanningScene>(
          "allow collision (object,table)");
      stage->allowCollisions(object_id, std::vector<std::string>{"table"},
                             true);
      grasp->insert(std::move(stage));
    }
    {
      // 3.6 lift
      RCLCPP_INFO(LOGGER, "[W3][lift] lifting object upward");
      auto stage = std::make_unique<mtc::stages::MoveRelative>(
          "lift object", cartesian_planner);
      stage->properties().configureInitFrom(mtc::Stage::PARENT, {"group"});
      stage->setMinMaxDistance(0.08, 0.15);
      stage->setIKFrame(hand_frame);
      stage->properties().set("marker_ns", "lift_object");

      // Set upward direction
      geometry_msgs::msg::Vector3Stamped vec;
      vec.header.frame_id = "world";
      vec.vector.z = 1.0;
      stage->setDirection(vec);
      grasp->insert(std::move(stage));
    }
    task.add(std::move(grasp));
  }

  // 4.connect between pick and place
  {
    RCLCPP_INFO(LOGGER, "[W3][connect] move to place");
    auto stage_between_pick_and_place = std::make_unique<mtc::stages::Connect>(
        "stage between pick and place",
        mtc::stages::Connect::GroupPlannerVector{
            {arm_group_name, sampling_planner},
            {hand_group_name, interpolation_planner}});

    stage_between_pick_and_place->setTimeout(5.0);
    stage_between_pick_and_place->properties().configureInitFrom(
        mtc::Stage::PARENT);

    task.add(std::move(stage_between_pick_and_place));
  }

  // 5.place
  {
    RCLCPP_INFO(LOGGER, "[W3][place] start the place ");
    auto place = std::make_unique<mtc::SerialContainer>("place object");
    task.properties().exposeTo(place->properties(),
                               {"eef", "group", "ik_frame"});
    place->properties().configureInitFrom(mtc::Stage::PARENT,
                                          {"eef", "group", "ik_frame"});
    {
      // 5.1 generate place pose
      auto stage = std::make_unique<mtc::stages::GeneratePlacePose>(
          "generate place pose");
      stage->properties().configureInitFrom(mtc::Stage::PARENT);
      stage->properties().set("marker_ns", "place_pose");
      stage->setObject(object_id);
      geometry_msgs::msg::PoseStamped target_pose_msg;
      target_pose_msg.header.frame_id = "world";
      target_pose_msg.pose.position.x = 0.45;
      target_pose_msg.pose.position.y = 0.20;
      target_pose_msg.pose.position.z = 0.26;
      target_pose_msg.pose.orientation.w = 1.0;
      stage->setPose(target_pose_msg);
      stage->setMonitoredStage(attach_object_stage);

      // 5.11 computeIK
      auto wrapper = std::make_unique<mtc::stages::ComputeIK>("place pose IK",
                                                              std::move(stage));
      wrapper->setMaxIKSolutions(2);
      wrapper->setMinSolutionDistance(1.0);
      wrapper->setIKFrame(object_id);
      wrapper->properties().configureInitFrom(mtc::Stage::PARENT,
                                              {"eef", "group"});

      //
      wrapper->properties().configureInitFrom(mtc::Stage::INTERFACE,
                                              {"target_pose"});

      place->insert(std::move(wrapper));
    }
    {
      // 5.2 open hand
      RCLCPP_INFO(LOGGER, "[W3][open hand] release object");
      auto stage = std::make_unique<mtc::stages::MoveTo>("open hand",
                                                         interpolation_planner);
      stage->setGroup(hand_group_name);
      stage->setGoal("open");
      place->insert(std::move(stage));
    }
    {
      // 5.3forbid collision
      RCLCPP_INFO(LOGGER,
                  "[W3][collision] forbid collision between hand and object");
      auto stage = std::make_unique<mtc::stages::ModifyPlanningScene>(
          "forbid collision (hand,object)");
      stage->allowCollisions(object_id,
                             task.getRobotModel()
                                 ->getJointModelGroup(hand_group_name)
                                 ->getLinkModelNamesWithCollisionGeometry(),
                             false);
      place->insert(std::move(stage));
    }
    {
      // 5.4 detach object
      RCLCPP_INFO(LOGGER, "[W3][detach object] detach object from hand");

      auto stage =
          std::make_unique<mtc::stages::ModifyPlanningScene>("detach object");
      stage->detachObject(object_id, hand_frame);
      place->insert(std::move(stage));
    }
    {
      RCLCPP_INFO(LOGGER,
                  "[W3][collision] restore box/table collision checking");
      auto stage = std::make_unique<mtc::stages::ModifyPlanningScene>(
          "forbid collision (object,table)");
      stage->allowCollisions(object_id, std::vector<std::string>{"table"},
                             false);
      place->insert(std::move(stage));
    }
    {
      // 5.5 retreat
      RCLCPP_INFO(LOGGER, "[W3][retreat] retreat after placing object");
      auto stage = std::make_unique<mtc::stages::MoveRelative>(
          "retreat", cartesian_planner);
      stage->properties().configureInitFrom(mtc::Stage::PARENT, {"group"});
      stage->properties().set("marker_ns", "retreat");
      stage->properties().set("link", hand_frame);
      stage->setIKFrame(hand_frame);
      stage->setMinMaxDistance(0.01, 0.12);
      geometry_msgs::msg::Vector3Stamped vec;
      vec.header.frame_id = hand_frame;
      vec.vector.z = -1.0;
      stage->setDirection(vec);
      place->insert(std::move(stage));
    }
    task.add(std::move(place));
  }

  return task;
}

int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  rclcpp::NodeOptions options;
  options.automatically_declare_parameters_from_overrides(true);
  auto desktop_pick_place = std::make_shared<DesktopPickPlace>(options);
  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(desktop_pick_place->getNodeBaseInterface());

  std::atomic_bool task_done{false};
  std::thread task_thread([&desktop_pick_place, &task_done]() {
    desktop_pick_place->setupPlanningScene();
    rclcpp::sleep_for(std::chrono::milliseconds(
        500)); //考虑到planning scene同步问题，稍微延迟一会。
    desktop_pick_place->doTask();
    RCLCPP_INFO(rclcpp::get_logger("desktop_pick_place"),
                "Task finished! Node is kept alive for RViz visualization. "
                "Press Ctrl+C to exit.");
    task_done.store(true);
  });

  while (rclcpp::ok() ) {
    executor.spin_some(std::chrono::milliseconds(100));
    std::this_thread::sleep_for(std::chrono::milliseconds(10));
  }

  if (task_thread.joinable())
    task_thread.join();

  rclcpp::shutdown();
  return 0;
}
