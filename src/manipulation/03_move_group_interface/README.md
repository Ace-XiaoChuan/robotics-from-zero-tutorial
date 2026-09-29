# 运动请求、笛卡尔路径与执行反馈

本文行数：178行，预期阅读时长：9分钟

**读一次 MoveGroupInterface 调用，要连着看“请求上下文 → 输入目标 → 规划输出 → 执行结果 → 状态反馈”。一个成功返回值只回答它所在环节的问题。**

**本章职责：** 说明单次运动请求如何表达、如何检查结果。规划原理与绘图几何分析见[第一章](../01_motion_planning/README.md)，配置来源见[第二章](../02_moveit_setup/README.md)，环境对象和碰撞关系见[第四章](../04_planning_scene/README.md)。

## 速记要点

- `MoveGroupInterface(node, "panda_arm")` 选择规划组；它不是电机驱动器，也不是为机器人另建一套模型。
- 位姿目标必须同时明确参考系、目标 link、位置和姿态；`Pose` 自身没有 `frame_id`。
- `setPoseTarget()` 设置目标，`plan()` 计算运动，`execute()` 提交已有轨迹；`move()` 把规划和执行合在一次请求中。
- `computeCartesianPath()` 返回请求路径的完成比例；它不能代替执行结果，也不会自动补完中断的路径。
- 一次接口对象可以保存目标、约束等设置。切换任务时要明确更新或清除旧设置，不能假设上次调用后自动全部清空。
- 轨迹数组按 `joint_names` 对应，`time_from_start` 是相对轨迹起点的时间；反馈还要对齐时间才能比较误差。

本页以 [hello_moveit.cpp](../packages/hello_moveit/src/hello_moveit.cpp) 和 [draw_line_and_circle.cpp](../packages/hello_moveit/src/draw_line_and_circle.cpp) 为源码依据。下面的改进流程属于说明，不表示已经改写或运行了这两个程序。

## 1. 一次请求有哪些上下文？

| 上下文 | 要回答的问题 | 本例或接口入口 |
| --- | --- | --- |
| 规划组 | 哪些关节参与运动？ | `panda_arm` |
| 模型与场景 | 使用哪台机器人、哪些障碍？ | 由实际 launch、模型参数和规划场景提供 |
| 起始状态 | 从哪个关节构型开始？ | 当前反馈，或显式 `setStartState()` |
| 位姿参考系 | 目标数值在哪个坐标系下表达？ | `getPoseReferenceFrame()`、`setPoseReferenceFrame()` |
| 目标 link | 哪个 link 的位姿要到达目标？ | `getEndEffectorLink()` 或显式指定 |
| 目标与容差 | 满足什么条件算到达？ | 关节目标、位姿目标、命名目标及对应容差 |
| 路径约束 | 中间过程必须维持什么？ | 例如全程保持工具朝向 |
| 规划与速度设置 | 搜索多久、如何缩放速度？ | 规划时间预算、速度和加速度缩放 |

`getPlanningFrame()` 返回规划模型使用的参考系，`getPoseReferenceFrame()` 表示接口解释相应位姿目标时使用的参考系；两者不应仅凭默认行为就视为永远相同。显式传入 `PoseStamped` 时也要确认该 frame 可以转换到模型需要的坐标系。

仓库源码另用 `panda_link0` 创建可视化工具。这个字符串确定的是相应可视化的参考上下文，不会自动给之后构造的所有 `Pose` 补上同样的 frame。

若只是预览假想构型之间的运动，可以显式指定规划起点；要实际执行，必须重新核对当前机器人状态与轨迹起点。常用的 `setStartStateToCurrentState()` 表达“采用当前状态作为起点”，但它不能弥补反馈缺失或过期。

接口语义按 [MoveGroupInterface Humble 头文件](https://raw.githubusercontent.com/moveit/moveit2/humble/moveit_ros/planning_interface/move_group_interface/include/moveit/move_group_interface/move_group_interface.h) 核对；具体重载应与安装版本一致。

## 2. 例子一：源码中的位姿目标表示什么？

[hello_moveit.cpp](../packages/hello_moveit/src/hello_moveit.cpp) 的目标节选如下：

```cpp
geometry_msgs::msg::Pose target;
target.position.x = 0.1;
target.position.y = 0.4;
target.position.z = 0.4;
target.orientation.y = 0.8;
target.orientation.w = 0.6;
move_group_interface.setPoseTarget(target);
```

**输入解释：** 位置为 `(0.1,0.4,0.4) m`；ROS 四元数按 `(x,y,z,w)` 为 `(0,0.8,0,0.6)`，未赋值的消息数值字段在这里保持零。

**静态推导：** 四元数模长为 `√(0.8²+0.6²)=1`。用轴角形式解释，这个四元数对应绕所用参考系的 Y 轴旋转：

```text
θ = 2 atan2(0.8, 0.6) ≈ 1.8546 rad ≈ 106.26°
```

它不是“Y 方向转 0.8 rad”，也不是欧拉角。目标约束的是被选中的末端 link；若任务真正关心笔尖或夹持中心，还需要考虑 TCP 偏移，见第二章的坐标例子。

**不能由这段代码推出的结论：** 该位姿在当前机器人上可达、没有碰撞、实际到达误差为零。源码没有在目标 `Pose` 中带上坐标系，阅读时仍需核对接口实际采用的参考系与目标 link。

### 目标与路径约束要分别表达

例如“终点姿态为这个四元数”只限制终点附近；“搬杯子时一直保持直立”需要路径约束。设置了路径约束后，规划起点也要满足约束，否则可能在开始搜索前就失败。

如果下一次请求不再需要旧约束，应明确 `clearPathConstraints()`；位姿目标可用 `clearPoseTargets()` 清理。这两个操作处理的对象不同，清目标不等于清路径约束。相关用法见 [Humble C++ 接口教程](https://moveit.picknik.ai/humble/doc/examples/move_group_interface/move_group_interface_tutorial.html)。

## 3. `plan()` 和 `execute()` 分别返回什么？

仓库的基础例子先把 `plan(msg)` 的返回值转成布尔量，再在成功分支调用 `execute(plan)`。这样区分了“是否获得计划”，但没有检查后一个调用的返回值。

| 调用或对象 | 含义 | 不能据此断言 |
| --- | --- | --- |
| 设置目标成功 | 接口接受相应目标设置 | 一定存在完整可行路径 |
| `plan(plan)` 成功 | 本次规划返回成功和计划 | 机器人已经运动 |
| `plan.trajectory_` | 规划输出的机器人轨迹 | 每个点都是实际测量值 |
| `publishTrajectoryLine(...)` | 显示规划路径 | 轨迹已经由控制器执行 |
| `execute(plan)` 成功 | 执行链报告该请求完成 | 绘图、接触或抓取任务必然成功 |

下面是**建议的逻辑伪代码**，省略了 ROS 初始化和具体错误类型，不作为已编译程序：

```text
确认当前状态可用，记录规划组、参考系和目标 link
设置本次目标、容差、约束与规划预算
调用 plan
若返回失败：记录规划错误，结束本次请求
检查轨迹非空、关节对应关系、终点和时间信息
执行前核对当前状态、场景与规划时是否仍相符
调用 execute，单独记录执行返回码
读取带时间的状态反馈，判断任务所需误差和结果
```

不能仅靠把日志写成 “Executing” 来判断执行成功。基础例子的可视化提示需要用户点击，等待期间如果机器人或环境变了，应重新确认旧计划的适用性。

## 4. 例子二：笛卡尔路点完成了多少？

绘图源码先沿参考系 `+Y` 增加 `0.15 m`，再生成半径 `0.05 m` 的圆形路点，保持原四元数不变。路点几何与约 `4.16 mm` 的首尾缺口已在[第一章绘图例子](../01_motion_planning/README.md#5-例子三仓库的直线加圆到底做了什么)推导，这里只看接口结果：

```cpp
const double eef_step = 0.01;
const double jump_threshold = 0.0;
moveit_msgs::msg::RobotTrajectory trajectory;
double fraction = move_group_interface.computeCartesianPath(
    waypoints, eef_step, jump_threshold, trajectory);
```

`eef_step` 的平移单位为 m，用于路径离散；它不是控制周期或末端速度。按本例的 Humble 重载，`jump_threshold=0` 禁用该项关节跳跃阈值检查，不表示关节变化必然平滑。

| 假设返回值 | 当前源码的行为 | 正确解读 |
| --- | --- | --- |
| `0.85` | 不进入执行分支 | 完成比例未超过代码阈值 |
| `0.90` | 不进入执行分支 | 使用的是严格大于 `0.9` |
| `0.95` | 将返回轨迹装入 Plan 并请求执行 | 允许提交部分路径 |
| `1.00` | 请求执行 | 请求路点已完整求解，实际执行结果仍需检查 |

这些是假设输入下的分支推导，不是测试得到的成功率。完整画图应要求完整生成所需几何，并检查轨迹和执行；即使比例接近 1，也应核对最后实际达到的路点，而不是把阈值直接当成任务完成定义。

将 `RobotTrajectory` 放进 `Plan` 是包装数据，不会自动补回缺失路径、闭合圆形或修复无效时间。也不要假定普通 `plan()` 的每个后处理和速度设置在另一条调用流程中都同样生效；应读取最终轨迹，并结合实际版本确认生成方式。

## 5. 例子三：怎样读轨迹中的时间和关节数组？

对于固定基座手臂，常查看 `RobotTrajectory.joint_trajectory`。以下是**人为构造的两转动关节消息示意**，顺序由 `joint_names` 明确给出：

```text
joint_names = [joint_a, joint_b]
```

| 点 | `time_from_start` / s | `positions` / rad |
| --- | --- | --- |
| 0 | 0.0 | `[0.0, 0.0]` |
| 1 | 0.5 | `[0.2, −0.1]` |
| 2 | 1.5 | `[0.4, −0.3]` |

**结果与解释：** 第二段时长是 `1.5−0.5=1.0 s`，不是 `1.5 s`。两段平均速度依次为 `[0.4,−0.2] rad/s` 和 `[0.2,−0.2] rad/s`。这些是位置差除以时间差所得的段平均值，不是控制器插值后每一时刻的瞬时速度。

实际点还可能带有 `velocities`、`accelerations` 或 `effort`。某字段为空表示未提供该数组，不能擅自当作所有数值均为零；哪些字段被接受取决于控制器接口。`time_from_start` 的定义见 [Humble JointTrajectoryPoint 消息](https://raw.githubusercontent.com/ros2/common_interfaces/humble/trajectory_msgs/msg/JointTrajectoryPoint.msg)。

检查普通多点运动轨迹时，至少确认点数组与关节名称维度一致、数值有限、时间顺序合理，并符合控制器要求。时间戳是执行安排，不能把它误当成已经发生的测量时间。

### 反馈怎样与目标比较？

假设在同一时刻 `t=1.5 s`，期望 `[joint_a,joint_b]=[0.4,−0.3] rad`，反馈消息却按 `[joint_b,joint_a]` 排列，值为 `[-0.29,0.38] rad`。

先按名称重排，实际值为 `[0.38,−0.29] rad`；误差 `q_desired−q_actual=[0.02,−0.01] rad`。直接按数组位置相减会得到完全错误的结论。实际比较还需以一致时钟和时间戳对齐，必要时对期望轨迹插值；连续转动关节还要处理角度周期。

末端位置误差则需要相同参考系和同一个工具点。把基座系中的期望 TCP 与相机系中的实际手爪原点相减，数值没有可比较的物理含义。

## 6. ROS 回调为什么也影响接口结果？

两个示例都把节点加入 executor，并用后台线程 `spin()`，主线程负责规划与执行。这里的 executor 用来处理状态、服务和 Action 等 ROS 回调；它与“机械臂执行轨迹”的执行器不是同一个概念。

因此，等待不到状态或结果时，除了机器人和控制器，还要检查节点是否在处理回调、反馈是否过期、模型参数是否加载一致。仅增加规划时间不能修复接口通信问题。

基础示例结束时先 `rclcpp::shutdown()` 再等待 spin 线程退出。阅读其他程序时也要区分“任务完成”和“节点停止”：任务函数返回不保证后台 `spin()` 自动结束。

## 7. 按结果定位失败环节

| 现象 | 优先查看 | 应保留的结果 |
| --- | --- | --- |
| 无法取得当前状态 | joint state 来源、时间、回调处理 | 缺失关节名、状态时间 |
| 目标被拒绝或无法求解 | 参考系、目标 link、姿态、IK 与限制 | 目标完整位姿、错误码 |
| `plan()` 失败 | 起点有效性、碰撞、约束、规划预算 | 规划错误与请求上下文 |
| 笛卡尔路径不完整 | 首个失败段、碰撞、IK 分支与奇异性 | 完成比例、终点、关节变化 |
| 规划成功但执行失败 | 控制器接口、起点差异、时间信息 | 单独的执行返回码 |
| 执行完成但误差大 | 反馈对齐、TCP、标定、控制跟踪 | 误差单位、参考系与时间区间 |

## 按需查阅与验证边界

[原始日志与详细笔记](history.md) 保留历史上下文；接口复习以本页的请求与结果链为入口。更完整的控制器对应关系见[第二章](../02_moveit_setup/README.md)，误差与跟踪算法见[控制专题](../../control/README.md)。

本页核对了本地源码分支、数值示例及 Humble 接口说明，未构建或运行 ROS / MoveIt。实际可达性、路径完成比例、返回轨迹的时间参数与执行误差均未测量；没有把示例表格当作运行记录。

[上一章：模型与配置](../02_moveit_setup/README.md) · [下一章：规划场景](../04_planning_scene/README.md) · [返回 MoveIt 目录](../README.md)
