// 注意：我认为在阅读此源代码时真正要死磕的是 stage
// 链的动作逻辑，不是每一个辅助函数的**内部实现**。

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

static const rclcpp::Logger LOGGER = rclcpp::get_logger("mtc_tutorial");
namespace mtc = moveit::task_constructor; // 指定命名空间别名

class MTCTaskNode {
public:
  MTCTaskNode(const rclcpp::NodeOptions &options);

  // 命名空间、子命名空间、类
  // SharedPtr：Typedef类型别名，意为：“请给我一个共享智能指针SharedPtr，这个指针指向一个
  // 基础节点接口类 (NodeBaseInterface)，这个类存放在 节点接口库
  // (node_interfaces) 中，而这个库属于 ROS 2 C++ 核心库 (rclcpp)。”
  rclcpp::node_interfaces::NodeBaseInterface::SharedPtr getNodeBaseInterface();

  void doTask();

  void setupPlanningScene();

private:
  mtc::Task createTask();
  mtc::Task task_;
  rclcpp::Node::SharedPtr node_;
};

// ---------
// 具体实现
// ---------

// std::make_shared<T>(args...)，把 std::make_shared
// 想象成一个“全能代工厂”，T为模板参数，
// (args...)是造对象需要的原材料。代工厂自己并不使用这些原材料，它会原封不动地把这些参数丢给
// rclcpp::Node 的构造函数。
MTCTaskNode::MTCTaskNode(const rclcpp::NodeOptions &options)
    : node_{std::make_shared<rclcpp::Node>("pick_and_place", options)} {}

// 这其实是一个getter函数。安全地把类内部私有的 ROS 2
// 节点中“最核心的基础通信部件”提取出来，交给外部的执行器（Executor）去驱动。
rclcpp::node_interfaces::NodeBaseInterface::SharedPtr
MTCTaskNode::getNodeBaseInterface() {
  return node_->get_node_base_interface();
}

void MTCTaskNode::setupPlanningScene() {
  moveit_msgs::msg::CollisionObject object;
  object.id = "object";
  object.header.frame_id = "world";
  // 易知 primitives 是 std::vector 类型(因为碰撞物体可以是复合形状)
  // resize(1): 把这个数组的长度强行设定为 1,标准化要付出代价：虽然只有一个元素
  // CYLINDER 也得用数组。
  object.primitives.resize(1);
  object.primitives[0].type = shape_msgs::msg::SolidPrimitive::CYLINDER;
  object.primitives[0].dimensions = {0.1,
                                     0.02}; // 参数是有严格顺序的:高度、半径

  geometry_msgs::msg::Pose pose;
  pose.position.x = 0.5;
  pose.position.y = -0.25;
  pose.orientation.w = 1.0;
  object.pose = pose;

  // 同步到机器人的大脑（规划场景）
  moveit::planning_interface::PlanningSceneInterface psi;
  psi.applyCollisionObject(object);
}

void MTCTaskNode::doTask() {
  task_ = createTask();

  // 1.判断task是否初始化成功
  try {
    task_.init();
  } catch (mtc::InitStageException &e) {
    RCLCPP_ERROR_STREAM(LOGGER, e);
    return;
  }

  // 尝试寻找最多 5 个完整任务解。plan ≠ execute；这里只规划，不执行。
  // plan(size_t max_solutions = 0UL) :
  // 找到max_solutions个规划,按照cost从小到大排序
  // .0UL:0、Unsigned、Long(无符号长整型)
  if (!task_.plan(5)) {
    RCLCPP_ERROR_STREAM(LOGGER, "Task planning failed");
    return;
  }
  // # solution文档详解：
  // task_.solutions() 返回按 cost 排序的解集合，front()
  // 取当前排序下最靠前的解，通常就是代价最低的那个。
  // 一句话总结：给我一份排好序的解决方案列表，我保证只看不改，而且给我指针(查看权)就行了，不用把整个数据抄给我。

  // inline（内联）—— 纯粹为了运行快
  // ordered<...>有序列表
  // SolutionBaseConstPtr 解决方案只读指针

  // # 链式调用
  // [修饰符与返回值] + [命名空间与名字] + [尾部修饰符]
  // ## 修饰符与返回值:
  // 1.inline内联修饰符
  // 2.ordered<...>（核心容器）：
  // 最重要的返回值:即一个名为ordered的容器(具有自动排序功能)
  // 3.const [类型] &:
  // 常 引用(&)
  // 如果 BigData& getData(),直接用引用操作原件,不安全.

  // ## 尾部修饰符 const
  // 尾巴上的 const 管的是这个函数本身，当一个函数后面跟了
  // const,表示这个函数纯读取、不篡改

  // ## 在 C++ 中，点号 . 和括号 () 的优先级比星号 *
  // 高。所以这句代码的真实结合顺序是这样的：
  // *(task_.solutions().front())

  // # cpp 调用顺序:
  // ## 从左到右:
  // 点号 . 和箭头 ->:
  // 从左到右。因为如果没有左边的对象，右边的函数根本不知道自己该给谁打工。

  // ## 套娃处理（从右到左、由内向外执行）
  // 涉及符号：星号 *（解引用）、取址号 &、函数嵌套 A(B(C))、等号 =

  // 将解决方案发布到 RViz 中进行可视化————如果您不需要可视化，可以删除此行。
  task_.introspection().publishSolution(
      *task_.solutions()
           .front()); // introspection()返回一个Introspection
                      // 对象的引用。这个对象拥有把内部复杂的 C++
                      // 矩阵数据，翻译成外部 ROS 2
                      // 消息（Message）的能力。publishSolution:把特定的方案打包成
                      // ROS Topic 广播出去.

  // 执行
  auto result = task_.execute(*task_.solutions().front());

  // 错误处理
  if (result.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS) {
    RCLCPP_ERROR_STREAM(LOGGER, "Task execution failed");
    return;
  }
  return;
}

mtc::Task MTCTaskNode::createTask() {
  mtc::Task task;
  // 返回task的最顶层的串行容器的指针。mtc::Task被实例化时，一定会默认的、强制的创建一个SerialContainer作为次级根容器
  task.stages()->setName("demo task");
  task.loadRobotModel(node_);

  // 注意：作为操作符（在表达式中）：如 ptr = &a;。这是取地址，把变量 a
  // 的内存地址赋给指针。 作为类型声明（在等号左边）：如 int& b = a; 或者 auto&
  // c = d;。这是声明一个引用，相当于给变量起了一个“别名”。 在 C++ 的 auto
  // 推导规则中，数组如果直接赋值，auto arm_group_name =
  // "panda_arm";会发生“退化（Array
  // Decay）”。它会丢失数组的长度信息，退化成一个普通的 C 风格指针 const
  // char*。虽然这样也能用，但这是一种隐式的类型转换。
  const auto &arm_group_name = "panda_arm";
  const auto &hand_group_name = "hand";
  const auto &hand_frame = "panda_hand";

  // 为当前整个任务（Task）设置一个全局属性（Property）。
  // 在 MTC
  // 的属性继承机制中，通过该函数设置的属性会默认向下传递给任务中的所有子容器和阶段（Stages），除非子阶段显式覆盖了该属性。
  // Parameters:name:属性的名称（键值）;value:属性的具体值.
  task.setProperty("group", arm_group_name);
  task.setProperty("eef", hand_group_name);
  task.setProperty("ik_frame", hand_frame);

  // 下面几行没有实践意义，可以删除。
  // 保存当前编译器的所有警告 / 报错设置状态（就像把当前状态压入一个栈里）。
#pragma GCC diagnostic push
  // 告诉编译器：“接下来的代码中，如果发现有变量被赋值了但根本没有被使用（unused-but-set-variable），请忽略它，不要打印警告信息。”
#pragma GCC diagnostic ignored "-Wunused-but-set-variable"
  // 这就是那行会引发警告的实际 C++ 代码。定义了一个指向 mtc::Stage
  // 的指针变量，并赋值为空。
  mtc::Stage *current_state_ptr = nullptr;
  // 恢复之前保存的编译器警告状态（从栈中弹出）。
#pragma GCC diagnostic pop

  auto stage_state_current =
      std::make_unique<mtc::stages::CurrentState>("current");
  current_state_ptr = stage_state_current.get();
  task.add(
      std::move(stage_state_current)); //这里 task 和 grasp -> insert 差不多。

  // ---
  // ## 一、定义三个规划器
  // ---

  // 1. 采样规划器 (PipelinePlanner) —— “绕障导航员”
  // 底层通常调用 OMPL（开源运动规划库），使用类似
  // RRT（快速探索随机树）这样的“采样算法”。 特点：具有全局视野，精通避障。
  // 但是它生成的轨迹在现实空间中不是直线的（机械臂可能会绕一个大圈来避开障碍物）。
  // 应用场景：大范围的自由移动（Freemove）。
  // 比如让机械臂从“初始位置”移动到“目标物体上方”。在这段长距离路程中，最重要的是“别撞到桌子或墙”，怎么走过去不重要。
  // (注：因为它需要调用底层的 MoveIt
  // 核心服务和参数服务器，所以它的构造函数必须传入 node_。)
  auto sampling_planner =
      std::make_shared<mtc::solvers::PipelinePlanner>(node_);

  // 2. 关节插值规划器 (JointInterpolationPlanner) —— “简单粗暴的电机驱动”
  // 这是一个非常轻量级、纯数学的规划器。
  // 特点：只在“关节空间”里走直线。
  // 它根本不管现实世界里的三维空间，只是单纯地让电机从 A 角度匀速转到 B
  // 角度。它本身不具备复杂的避障能力。 应用场景：非常简单、已知安全的微小动作。
  // 最典型的场景就是控制夹爪（手爪）的开合。让夹爪张开，不需要什么高深的避障算法，直接让夹爪关节张开就行了。所以你在前面的代码中，打开手爪（stage_open_hand）传的就是这个
  // interpolation_planner。
  auto interpolation_planner =
      std::make_shared<mtc::solvers::JointInterpolationPlanner>();

  // 3. 笛卡尔规划器 (CartesianPath) —— “高精度直尺”
  // 现实物理空间（笛卡尔空间）里的直线规划器。
  // 特点：强制机械臂的末端（比如手爪）在现实空间中走一条笔直的直线。
  // 它通过不断地逆运动学（IK）求解，算出沿着直线走的每一个微小步长（你在前面代码里设置了
  // setStepSize(.01) 即 1厘米一步）。
  // 应用场景：精密操作（接近和撤离）。比如抓杯子时：手爪已经到了杯子上方，最后下降的那
  // 10 厘米，必须是笔直向下的。如果这时候用前面的
  // PipelinePlanner，手爪可能会划一道弧线，直接把杯子碰倒。比如插拔 U
  // 盘、在黑板上画直线，都必须用这个规划器。
  auto cartesian_planner = std::make_shared<mtc::solvers::CartesianPath>();
  cartesian_planner->setMaxVelocityScalingFactor(
      1.0); // 设置最大速度缩放比例(100%)。
  cartesian_planner->setMaxAccelerationScalingFactor(
      1.0);                            // 设置最大加速度缩放比例。
  cartesian_planner->setStepSize(.01); // 设置笛卡尔空间插值的步长(.01=1cm)。

  // ---
  // ## 二、开始定义stages
  // ---
  /*
  current
  → open hand
  → move to pick
  → pick object
      → approach object
      → generate grasp pose + grasp pose IK
      → allow collision
      → close hand
      → attach object
      → lift object
  → move to place
  → place object
      → generate place pose + place pose IK
      → open hand
      → forbid collision
      → detach object
      → retreat
  → return home
  */

  /*
  函数类型	    作用	                                    例子

  选择控制对象	这个 stage 控制机械臂还是夹爪	            setGroup()
  设置目标	    要到哪个姿态 / 状态 / 方向
  setGoal()、setDirection()、setPose() 设置求解器行为
  用哪个planner、尝试多少解、步长多少
  setTimeout()、setMaxIKSolutions()、setStepSize() 设置属性传递	从父 stage
  或接口继承哪些信息	            configureInitFrom()、exposeTo() 修改规划世界
  改碰撞、附着、分离物体 allowCollisions()、attachObject()、detachObject()
  */

  auto stage_open_hand =
      std::make_unique<mtc::stages::MoveTo>("open hand", interpolation_planner);
  stage_open_hand->setGroup(hand_group_name);
  stage_open_hand->setGoal("open");
  task.add(std::move(stage_open_hand));

  // 注意：C++ 普通函数调用没有“按名字/按类型自动分配参数”的机制，这里 move to
  // pick 的const char [13] 是隐式类型转换。而且形参非const引用不行，因为临时
  // std::string 不能绑定到普通的非 const 左值引用。
  // ---
  // ### Connect("move to pick")
  // ---
  auto stage_move_to_pick = std::make_unique<mtc::stages::Connect>(
      "move to pick", mtc::stages::Connect::GroupPlannerVector{
                          {arm_group_name, sampling_planner}});
  stage_move_to_pick->setTimeout(5.0);
  stage_move_to_pick->properties().configureInitFrom(
      mtc::Stage::
          PARENT); // properties
                   // 可以理解为一个stage、task、solver的参数字典。它不是
                   // ROS parameter，而是 MoveIt Task Constructor
                   // 自己的一套属性系统，用来在不同 stage
                   // 之间传递和配置数据。
  task.add(std::move(stage_move_to_pick));

  // ### attach_object_stage 指针
  mtc::Stage *attach_object_stage =
      nullptr; // Forward attach_object_stage to place pose generator

  // 在 C++ 里，花括号不只属于 if、for、while、函数、类。只要语法位置合法，{}
  // 这种“单独成块”的用法可以使用。它叫做 局部作用域 / 代码块 / block scope。
  {
    // 创建串行容器 pick object,放所有和抓取有关的 stage。
    auto grasp = std::make_unique<mtc::SerialContainer>("pick object");
    // exposeTo() 把 task 里的全局属性暴露给 grasp 容器。所以 grasp 里面的 stage
    // 就可以继承这些属性，不用每个 stage 都重复写。
    task.properties().exposeTo(grasp->properties(),
                               {"eef", "group", "ik_frame"});
    grasp->properties().configureInitFrom(
        mtc::Stage::PARENT,
        {"eef", "group",
         "ik_frame"}); // 让当前 stage 的 properties 在初始化时，从父级 stage /
                       // 父级容器 / task 继承名为 "group" 的属性。

    // ### MoveRelative("approach object")
    // 沿 hand_frame 坐标系的 +Z 方向移动 10cm 到 15cm。
    // 在本示例的抓取姿态设置下，这个方向被用作接近物体的方向。
    // 注意：这里的 +Z 是手爪坐标系的 +Z，不一定等同于世界坐标中的“向前”。
    {
      auto stage =
          std::make_unique<mtc::stages::MoveRelative>( // 创建相对运动 stage
              "approach object", cartesian_planner);
      stage->properties().set(
          "marker_ns", "approach_object"); // marker_ns:RViz 可视化 marker
                                           // 的命名空间，不是核心逻辑
      stage->properties().set("link", hand_frame);
      stage->properties().configureInitFrom(mtc::Stage::PARENT, {"group"});
      stage->setMinMaxDistance(0.1, 0.15);

      geometry_msgs::msg::Vector3Stamped vec;
      vec.header.frame_id = hand_frame;
      vec.vector.z = 1.0;

      stage->setDirection(vec);
      // stage 转为右值，里面的所有权已经被移动走了，后面不能再用这个 stage
      // 指针。重新定义一个新的 stage
      // 是可以的，但必须在新的作用域里，或者换名字。它的意思是：我明确放弃
      // stage 对这个对象的所有权，把所有权转交给 grasp 容器。
      // grasp->insert(stage);这句是不行的！这等于把unique_ptr复制一份传进去。
      // **另外这里再强调一次：不要读成：grasp 指向 insert!**
      // 应该读成：grasp 指向的那个对象，调用 insert 进行插入 ContainerBase
      grasp->insert(std::move(stage));
    }

    // GenerateGraspPose 围绕 object 生成一批“手爪应该放在哪里”的候选末端位姿
    // 不是只尝试一个抓取角度，而是围着物体尝试很多个抓取角度。
    {
      auto stage = std::make_unique<mtc::stages::GenerateGraspPose>(
          "generate grasp pose");

      stage->properties().configureInitFrom(mtc::Stage::PARENT);
      stage->properties().set("marker_ns", "grasp_pose");

      stage->setPreGraspPose(
          "open"); //生成抓取候选时，假定夹爪预抓取姿态是 open
      stage->setObject("object");      //围绕哪个物体生成抓取姿态
      stage->setAngleDelta(M_PI / 12); //每隔 15 度采样一个抓取角度
      stage->setMonitoredStage(
          current_state_ptr); //监听某个 stage
                              //的状态，通常用于拿到物体/场景相关信息

      Eigen::Isometry3d grasp_frame_transform;
      Eigen::Quaterniond q =
          Eigen::AngleAxisd(M_PI / 2, Eigen::Vector3d::UnitX()) *
          Eigen::AngleAxisd(M_PI / 2, Eigen::Vector3d::UnitY()) *
          Eigen::AngleAxisd(M_PI / 2, Eigen::Vector3d::UnitZ());
      grasp_frame_transform.linear() = q.matrix();
      grasp_frame_transform.translation().z() = 0.1;

      // Compute IK
      // wrapper(包装器)
      auto wrapper = std::make_unique<mtc::stages::ComputeIK>("grasp pose IK",
                                                              std::move(stage));
      wrapper->setMaxIKSolutions(8); //每个目标最多保留 8 个 IK 解
      wrapper->setMinSolutionDistance(
          1.0); // IK 解之间要有足够差异，避免一堆几乎一样的解
      wrapper->setIKFrame(
          grasp_frame_transform,
          hand_frame); //定义 IK 目标对应的是手爪上的哪个坐标框架
      wrapper->properties().configureInitFrom(mtc::Stage::PARENT,
                                              {"eef", "group"});
      wrapper->properties().configureInitFrom(
          mtc::Stage::INTERFACE,
          {"target_pose"}); // GenerateGraspPose 生成了一个
                            // target_pose；ComputeIK 需要读取这个 target_pose；
                            // 所以让 ComputeIK 从接口状态里继承target_pose。
      grasp->insert(std::move(wrapper));
    }

    // 允许手爪和物体碰撞
    // 抓物体的时候，手爪一定会接触物体。默认情况下，MoveIt
    // 会把这种接触当成碰撞，认为路径非法。所以要临时允许：
    {
      auto stage = std::make_unique<mtc::stages::ModifyPlanningScene>(
          "allow collision (hand,object)");
      // 允许 object 和 hand 的所有带碰撞几何的 link 发生接触。
      stage->allowCollisions("object",
                             task.getRobotModel()
                                 ->getJointModelGroup(hand_group_name)
                                 ->getLinkModelNamesWithCollisionGeometry(),
                             true);
      grasp->insert(std::move(stage));
    }

    // 关闭手爪
    // 这一步很简单：把 hand 这个 group 移动到 SRDF 里定义的 close 姿态。
    {
      auto stage = std::make_unique<mtc::stages::MoveTo>("close hand",
                                                         interpolation_planner);
      stage->setGroup(hand_group_name);
      stage->setGoal("close");
      grasp->insert(std::move(stage));
    }

    // attach object：让物体“粘”到手爪上
    // 这一步非常关键。在关闭手爪之后，物体在规划场景里仍然只是一个普通碰撞物体。如果不
    // attach，它不会跟着手爪走。
    {
      auto stage =
          std::make_unique<mtc::stages::ModifyPlanningScene>("attach object");
      stage->attachObject("object", hand_frame);
      attach_object_stage = stage.get();
      grasp->insert(std::move(stage));
    }

    // lift object：抬起物体
    // 这一步意思是：抓住物体后，沿 world 坐标系的 z 正方向抬起 10cm 到 30cm。
    // 注意这里和 approach 不一样：approach：沿手爪自己的 z
    // 方向前进;lift：沿世界坐标系的 z 方向向上抬
    {
      auto stage = std::make_unique<mtc::stages::MoveRelative>(
          "lift object", cartesian_planner);
      stage->properties().configureInitFrom(mtc::Stage::PARENT, {"group"});
      stage->setMinMaxDistance(0.1, 0.3);
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

    {
      auto stage_move_to_place = std::make_unique<mtc::stages::Connect>(
          "move to place", mtc::stages::Connect::GroupPlannerVector{
                               {arm_group_name, sampling_planner},
                               {hand_group_name, interpolation_planner}});

      stage_move_to_place->setTimeout(5.0);
      stage_move_to_place->properties().configureInitFrom(mtc::Stage::PARENT);

      task.add(std::move(stage_move_to_place));
    }
    {
      auto place = std::make_unique<mtc::SerialContainer>("place object");

      task.properties().exposeTo(place->properties(),
                                 {"eef", "group", "ik_frame"});
      place->properties().configureInitFrom(mtc::Stage::PARENT,
                                            {"eef", "group", "ik_frame"});

      {
        auto stage = std::make_unique<mtc::stages::GeneratePlacePose>(
            "generate place pose");
        stage->properties().configureInitFrom(mtc::Stage::PARENT);
        stage->properties().set("marker_ns", "place_pose");
        stage->setObject("object");

        // 设置放置目标位姿。这里 pose 的参考坐标系是 "object"。
        // position.y = 0.5 表示目标放置位姿相对于 object frame 有一个 y
        // 方向偏移。 GeneratePlacePose 会结合被监控的 attach_object_stage
        // 来生成可用于放置的目标姿态。
        geometry_msgs::msg::PoseStamped target_pose_msg;
        target_pose_msg.header.frame_id = "object";
        target_pose_msg.pose.position.y = 0.5;
        target_pose_msg.pose.orientation.w = 1.0;
        stage->setPose(target_pose_msg);
        stage->setMonitoredStage(attach_object_stage);

        auto wrapper = std::make_unique<mtc::stages::ComputeIK>(
            "place pose IK",
            std::move(stage)); //包住目标生成器，对它生成的目标做 IK
        wrapper->setMaxIKSolutions(2); //每个目标最多保留 2 个 IK 解
        wrapper->setMinSolutionDistance(
            1.0); // IK 解之间要有足够差异，避免一堆几乎一样的解
        wrapper->setIKFrame("object");
        wrapper->properties().configureInitFrom(mtc::Stage::PARENT,
                                                {"eef", "group"});

        //
        wrapper->properties().configureInitFrom(mtc::Stage::INTERFACE,
                                                {"target_pose"});

        place->insert(std::move(wrapper));
      }

      {
        auto stage = std::make_unique<mtc::stages::MoveTo>(
            "open hand", interpolation_planner);
        stage->setGroup(hand_group_name);
        stage->setGoal("open");
        place->insert(std::move(stage));
      }

      {
        auto stage = std::make_unique<mtc::stages::ModifyPlanningScene>(
            "forbid collision (hand,object)");
        stage->allowCollisions("object",
                               task.getRobotModel()
                                   ->getJointModelGroup(hand_group_name)
                                   ->getLinkModelNamesWithCollisionGeometry(),
                               false);
        place->insert(std::move(stage));
      }

      {
        auto stage =
            std::make_unique<mtc::stages::ModifyPlanningScene>("detach object");
        stage->detachObject("object", hand_frame);
        place->insert(std::move(stage));
      }

      {
        auto stage = std::make_unique<mtc::stages::MoveRelative>(
            "retreat", cartesian_planner);
        stage->properties().configureInitFrom(mtc::Stage::PARENT, {"group"});
        stage->setMinMaxDistance(0.1, 0.3);
        stage->setIKFrame(hand_frame);
        stage->properties().set("marker_ns", "retreat");

        geometry_msgs::msg::Vector3Stamped vec;
        vec.header.frame_id = "world";
        vec.vector.x = -0.5;
        stage->setDirection(vec);

        place->insert(std::move(stage));
      }

      task.add(std::move(place));
    }
    {
      auto stage = std::make_unique<mtc::stages::MoveTo>("return home",
                                                         interpolation_planner);
      stage->properties().configureInitFrom(mtc::Stage::PARENT, {"group"});
      // 这里使用 JointInterpolationPlanner 回到
      // ready，适合已知简单、安全的关节空间移动。
      // 如果环境复杂或需要避障，更稳妥的做法可能是使用 sampling_planner。
      stage->setGoal("ready");
      task.add(std::move(stage));
    }
    return task;
  }
}

int main(int argc, char **argv) {
  rclcpp::init(argc, argv);

  rclcpp::NodeOptions options;
  options.automatically_declare_parameters_from_overrides(true);
  auto mtc_task_node = std::make_shared<MTCTaskNode>(options);
  rclcpp::executors::MultiThreadedExecutor executor;

  auto spin_thread =
      std::make_unique<std::thread>([&executor, &mtc_task_node]() {
        executor.add_node(mtc_task_node->getNodeBaseInterface());
        executor.spin();
        executor.remove_node(mtc_task_node->getNodeBaseInterface());
      });

  mtc_task_node->setupPlanningScene();
  mtc_task_node->doTask();

  // 这里没有取消执行器(executor.cancel();)，以保持节点运行，以便在RViz中检查解决方案。

  // 这里盘点一下: cpp 线程操作(std::thread 的 join() / detach()) 与 ROS 2
  // 执行器操作 executor.spin() / cancel() / add_node() / remove_node()
  // join():主线程会卡在这里，直到子线程函数返回。
  // detach():让线程独立运行，主线程不再等待它，也不再管理它。
  // joinable():检查这个线程是否还能被 join() 或 detach()。

  // add_node():把这个节点加入 executor，让 executor 开始管理它的回调。
  // spin():持续处理 executor 中节点的回调，直到 executor 被取消或 ROS 关闭。
  // cancel():请求 executor 停止 spin。
  // remove_node():把节点从 executor 中移除。
  spin_thread->join();
  rclcpp::shutdown();
  return 0;
}