#include <rclcpp/rclcpp.hpp>
#include <moveit/planning_scene/planning_scene.h>
#include <moveit/planning_scene_interface/planning_scene_interface.h>
#include <moveit/task_constructor/task.h>
#include <moveit/task_constructor/solvers.h>
#include <moveit/task_constructor/stages.h>

// 这里是为了兼容不同版本的 ROS 2 (例如 Humble 和较老的 Foxy 路径不同)
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

// 创建一个日志记录器，方便打印信息
static const rclcpp::Logger LOGGER = rclcpp::get_logger("mtc_tutorial");
namespace mtc = moveit::task_constructor;

// 定义一个类，把 ROS 节点和 MTC 任务封装起来
class MTCTaskNode
{
public:
  MTCTaskNode(const rclcpp::NodeOptions &options);

  // 暴露内部 ROS 节点的底层接口，主要用于交给 Executor 进行多线程调度
  rclcpp::node_interfaces::NodeBaseInterface::SharedPtr getNodeBaseInterface();

  // 执行任务的核心流程（初始化、规划、执行）
  void doTask();

  // 在环境中添加障碍物/抓取物
  void setupPlanningScene();

private:
  // 创建具体的 MTC 任务流水线（定义机器人要干嘛）
  mtc::Task createTask();

  mtc::Task task_;               // MTC 任务对象，存放规划阶段的流水线
  rclcpp::Node::SharedPtr node_; // 内部维护的一个真正的 ROS 2 节点
};

// 获取底层节点接口的实现
rclcpp::node_interfaces::NodeBaseInterface::SharedPtr MTCTaskNode::getNodeBaseInterface()
{
  return node_->get_node_base_interface();
}

// 构造函数：初始化内部的 ROS 2 节点，名字叫 "mtc_node"
MTCTaskNode::MTCTaskNode(const rclcpp::NodeOptions &options)
    : node_{std::make_shared<rclcpp::Node>("mtc_node", options)}
{
}

// 设置规划场景（在虚拟环境里放一个圆柱体）
void MTCTaskNode::setupPlanningScene()
{
  moveit_msgs::msg::CollisionObject object;
  object.id = "object";             // 物体的唯一名字
  object.header.frame_id = "world"; // 物体所在的坐标系

  // 定义物体的形状：圆柱体 (CYLINDER)
  object.primitives.resize(1);
  object.primitives[0].type = shape_msgs::msg::SolidPrimitive::CYLINDER;
  object.primitives[0].dimensions = {0.1, 0.02}; // 高0.1m，半径0.02m

  // 定义物体的位置和姿态
  geometry_msgs::msg::Pose pose;
  pose.position.x = 0.5;
  pose.position.y = -0.25;
  pose.orientation.w = 1.0;
  object.pose = pose;

  // 使用 PlanningSceneInterface 把物体发送给 MoveIt，让机器人在规划时知道避开它或者抓取它
  moveit::planning_interface::PlanningSceneInterface psi;
  psi.applyCollisionObject(object);
}

// 控制 MTC 任务的执行流程
void MTCTaskNode::doTask()
{
  // 1. 构建任务流水线
  task_ = createTask();

  try
  {
    // 2. 初始化任务。这步会检查你定义的各个 Stage 是否合法，参数是否给齐了
    task_.init();
  }
  catch (mtc::InitStageException &e)
  {
    RCLCPP_ERROR_STREAM(LOGGER, e);
    return;
  }

  // 3. 开始规划任务。参数 '5' 表示最多尝试寻找 5 条可行的完整运动轨迹
  if (!task_.plan(5))
  {
    RCLCPP_ERROR_STREAM(LOGGER, "Task planning failed"); // 如果找不到可行路径，就报错退出
    return;
  }

  // 4. 将规划好的第 1 条结果发布出去，这样你就可以在 RViz 里面看到动画演示了
  task_.introspection().publishSolution(*task_.solutions().front());

  // 5. 让真实的机械臂（或Gazebo仿真里的机械臂）去执行这第 1 条轨迹
  auto result = task_.execute(*task_.solutions().front());
  if (result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS) // 这其实是一个依赖关系
  {
    RCLCPP_ERROR_STREAM(LOGGER, "Task execution failed");
    return;
  }

  return;
}

// 核心函数：定义机器人具体怎么动的流水线 (Pipeline)
mtc::Task MTCTaskNode::createTask()
{
  mtc::Task task;
  task.stages()->setName("demo task"); // 给任务起个名字
  task.loadRobotModel(node_);          // 加载机器人的 URDF 和 SRDF 模型，这样 MTC 才认识机器人的关节

  // 定义一些后续会频繁使用的名字（根据你的具体机械臂配置而定，这里是 panda 机械臂）
  const auto &arm_group_name = "panda_arm"; // 手臂规划组
  const auto &hand_group_name = "hand";     // 夹爪规划组
  const auto &hand_frame = "panda_hand";    // 夹爪的坐标系(TCP)

  // 告诉 task，我们主要用哪个部位进行规划
  task.setProperty("group", arm_group_name);
  task.setProperty("eef", hand_group_name);
  task.setProperty("ik_frame", hand_frame);

// 这段是消除编译器的 "变量定义了但没使用" 的警告。
// 在后续更复杂的代码中，这个 current_state_ptr 会被传递给其他阶段。
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-but-set-variable"
  mtc::Stage *current_state_ptr = nullptr;
#pragma GCC diagnostic pop

  // ------------------------------------------------------------------
  // 【MTC 的核心概念：Stage (阶段)】
  // MTC 是像搭积木一样，把复杂任务拆成一个个小 Stage 串联起来。
  // ------------------------------------------------------------------

  // 积木 1：获取机器人当前的状态（也就是机器人现在停在哪里）
  // 所有的任务都必须从一个已知状态开始
  auto stage_state_current = std::make_unique<mtc::stages::CurrentState>("current");
  current_state_ptr = stage_state_current.get();
  task.add(std::move(stage_state_current)); // 把这块积木加进 task 里

  // ------------------------------------------------------------------
  // 【MTC 的核心概念：Solvers (求解器)】
  // 求解器就是计算“怎么从A点移动到B点”的算法。这里定义了三种常用的求解器。
  // ------------------------------------------------------------------
  // 1. PipelinePlanner: 调用 MoveIt 的默认规划算法(通常是OMPL)，适用于长距离、大范围、需要避障的运动。
  auto sampling_planner = std::make_shared<mtc::solvers::PipelinePlanner>(node_);
  // 2. JointInterpolationPlanner: 简单的关节插值，就是各关节匀速从A转到B，通常用于简单的、无障碍的动作（比如张开/闭合夹爪）。
  auto interpolation_planner = std::make_shared<mtc::solvers::JointInterpolationPlanner>();
  // 3. CartesianPath: 笛卡尔直线/圆弧规划，保证末端走直线，常用于抓取前靠近物体的最后一段距离。
  auto cartesian_planner = std::make_shared<mtc::solvers::CartesianPath>();

  // 限制一下笛卡尔运动的速度和加速度，以及插补的步长
  cartesian_planner->setMaxVelocityScalingFactor(1.0);
  cartesian_planner->setMaxAccelerationScalingFactor(1.0);
  cartesian_planner->setStepSize(.01);

  // 积木 2：移动到一个特定的状态（这里是张开夹爪）
  // 使用 MoveTo 这个预置的 Stage。要求使用上面的 interpolation_planner（关节插值求解器）来计算。
  auto stage_open_hand =
      std::make_unique<mtc::stages::MoveTo>("open hand", interpolation_planner);
  stage_open_hand->setGroup(hand_group_name); // 指定要动的是夹爪 (hand)
  stage_open_hand->setGoal("open");           // "open" 是在机器人的 SRDF 文件里预先定义好的固定姿态名字
  task.add(std::move(stage_open_hand));       // 把这块积木加进 task 里

  // 这个简单的例子目前只搭了2块积木：读取当前状态 -> 张开夹爪。
  return task;
}

int main(int argc, char **argv)
{
  // 初始化 ROS 2
  rclcpp::init(argc, argv);

  // 允许节点自动从启动文件/命令行参数中读取配置
  rclcpp::NodeOptions options;
  options.automatically_declare_parameters_from_overrides(true);

  // 实例化我们上面定义的管理类。
  // 它相当于一个控制器，管理着 ROS 节点和 MTC 任务逻辑。
  auto mtc_task_node = std::make_shared<MTCTaskNode>(options);

  // 创建一个多线程执行器。它的作用是并发处理 ROS 2 的各种回调（消息、服务、动作）
  rclcpp::executors::MultiThreadedExecutor executor;

  // 开启一个后台线程来专门处理 ROS 消息 (spin)
  auto spin_thread = std::make_unique<std::thread>([&executor, &mtc_task_node]()
                                                   {
    executor.add_node(mtc_task_node->getNodeBaseInterface()); // 把节点交给执行器
    executor.spin();                                          // 开始死循环监听处理消息
    executor.remove_node(mtc_task_node->getNodeBaseInterface()); });

  // 主线程继续往下走
  mtc_task_node->setupPlanningScene(); // 1. 布置场景（放一个圆柱体）
  mtc_task_node->doTask();             // 2. 规划并执行任务（读取状态 -> 规划 -> 执行张开夹爪）

  // doTask() 执行完毕后，等待后台处理消息的线程安全结束
  spin_thread->join();

  // 关闭 ROS 2
  rclcpp::shutdown();
  return 0;
}