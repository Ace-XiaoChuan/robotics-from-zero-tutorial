# MTC：多阶段任务规划

本文行数：200行，预期阅读时长：10分钟

**MoveIt Task Constructor（MTC）把任务拆成阶段，并在候选机器人状态与规划场景之间寻找能够完整连接的解。它既组织运动，也组织抓取前后物体关系的变化。**

解释 Task、Stage、求解器、属性传递、候选解与失败定位。场景操作的含义见[第四章](../04_planning_scene/README.md)，完整抓放的物理条件和结果判断见[第六章](../06_pick_place/README.md)。

## 速记要点

- Stage 表达一个子问题，solver 负责该子问题需要的运动求解；不是每个 Stage 都会生成机器人运动。
- 阶段之间传递的不只是关节角，还包括规划场景以及相关属性，例如物体是否已附着。
- 任务的执行顺序可以从前向后读，规划计算却可能从候选抓取状态向前、向后扩展，再连接两侧。
- 抓取位姿有 IK 解、接近路径可行、搬运可行，是不同筛选条件；局部成功不等于完整任务有解。
- 属性不会因为设置在 Task 上就无条件进入所有子阶段。要查看显式设置、父级初始化和接口属性来源。
- `init()`、`plan()`、`execute()` 分别检查不同环节，发布 RViz 解也不等于执行。

## 1. Task、Stage 和接口状态怎样组成任务？

| 概念 | 表达什么 | 本地例子 |
| --- | --- | --- |
| Task | 顶层任务，包含阶段结构、模型和求解结果 | `demo task`、`desktop_pick_place` |
| Stage | 一个生成、传播、连接或修改状态的步骤 | `CurrentState`、`MoveTo`、`Connect` |
| InterfaceState | 阶段边界上的场景及属性 | 抓取前、附着后等不同状态 |
| Solution / SubTrajectory | 连接状态的解及代价；可以包含轨迹或场景修改 | 手爪闭合轨迹、物体附着变化 |
| Container | 将多个阶段组织成更大的问题 | `SerialContainer("pick object")` |
| Solver | 某些运动阶段调用的求解方法 | `PipelinePlanner`、`CartesianPath` |

例如两个状态的手臂关节角完全相同，但一个状态中物体还在桌上，另一个状态中物体已附着，它们对后续抬升与碰撞检查的含义不同。不能把任务状态缩减成一个 `q` 数组。

`SerialContainer` 要求子阶段能组成连贯序列；更复杂任务也可以组织备选分支，但本仓库这些案例主要使用串行容器。本页不要求先学完所有容器类型。基础分类参见 [MTC Basic Concepts](https://moveit.github.io/moveit_task_constructor/basics.html)。

## 2. 例子一：入门程序到底包含几个动作？

[mtc_node.cpp](../packages/mtc_tutorial/src/mtc_node.cpp) 实际加入任务的阶段是：

```text
CurrentState("current")
    ↓
MoveTo("open hand", JointInterpolationPlanner)
    group = "hand"
    goal = "open"
```

**输入：** 机器人模型、当前场景和手爪组的 `open` 命名目标。

**静态结果：** 这个任务只尝试读取当前状态并张开手爪。源码创建了采样与笛卡尔求解器，但没有把使用它们的抓取或搬运阶段加入该任务。即使场景里有圆柱 `object`，也不能说程序已规划了抓取圆柱。

同样，[分层案例的 TaskBuilder](../packages/mtc_advanced_demo/src/task_builder.cpp) 当前也只组装这两个阶段。目录名 `advanced` 表达了代码组织方式的进一步拆分，不代表已有更完整的任务动作。

这两个事实也说明：看案例时优先找实际的 `task.add()` / 容器 `insert()`，再看对象和 solver 的声明。声明了什么不等于执行流程使用了什么。

## 3. 常见阶段怎样分工？

| 阶段 | 输入与输出的作用 | 典型问题 |
| --- | --- | --- |
| `CurrentState` | 产生当前机器人与场景状态 | 当前状态能否获得并用于规划？ |
| `MoveTo` | 从一侧状态求到指定目标的运动 | 手爪怎样到达 `open` 或 `close`？ |
| `MoveRelative` | 沿指定坐标系中的方向产生相对运动 | 沿工具轴接近、沿世界 Z 轴抬升 |
| `GenerateGraspPose` | 在被监视的场景基础上生成抓取位姿候选 | 从哪些方向抓这个物体？ |
| `ComputeIK` | 包装位姿生成阶段，为候选位姿求关节解 | 同一个抓取位姿有哪些合法构型？ |
| `Connect` | 尝试连接左右已知的状态 | 初始状态怎样到达某个预抓取构型？ |
| `ModifyPlanningScene` | 修改场景关系或碰撞规则 | 允许接触、附着、分离 |
| `GeneratePlacePose` | 根据相关场景和目标生成放置位姿 | 携带物体如何到达放置目标？ |

这里的“生成位姿”属于规划搜索，不会让真实物体移动。`ModifyPlanningScene` 也可以不产生关节位移，却对后续运动的碰撞检查至关重要。

### 阶段与 solver 要搭配看

| Solver | 本例的主要用途 | 不能误读为 |
| --- | --- | --- |
| `PipelinePlanner` | 大范围的到达与搬运连接，调用配置的规划流水线 | 固定等同于某个 RRT 变体 |
| `JointInterpolationPlanner` | 关节空间插值，如手爪开合 | 电机必定匀速，或完全不做碰撞检查 |
| `CartesianPath` | 接近、抬升和撤离等指定方向运动 | 通用绕障搜索，或天然拥有任意圆弧任务语义 |

尤其是关节插值：Humble 实现会检查沿途碰撞、关节限位，并可进行时间参数化；它缺少主动绕障搜索能力，不代表“忽略障碍直接驱动”。这比本地部分源码注释中的“各关节匀速转动”更准确，参见 [MTC Humble 插值求解器实现](https://raw.githubusercontent.com/moveit/moveit_task_constructor/humble/core/src/solvers/joint_interpolation.cpp)。

## 4. 例子二：为什么接近阶段写在抓取位姿生成之前？

[完整抓放源码](../packages/hello_moveit/src/pick_and_place.cpp) 中，抓取容器的顺序是：

```text
approach object
generate grasp pose + ComputeIK
allow collision → close hand → attach object → lift object
```

`allow collision` 允许指定手爪与物体接触。这个顺序表示最终执行的逻辑关系；位姿生成与 IK 为规划提供中间候选，本身不是额外执行一个“生成姿态动作”。

**计算思路：** 先生成一个抓取末端位姿并求出抓取构型，再从该候选向后推导接近运动的起点，得到预抓取状态；`Connect` 随后尝试把当前状态连接到这个预抓取状态。抓取后的闭合、附着和抬升则可沿另一侧继续传播。

因此，MTC 不是简单地按 C++ 添加顺序依次执行每个规划函数；`MoveRelative` 这样的传播阶段可以根据接口状态向不同方向求解。反向规划也不表示真实执行时机械臂反着完成任务。

### 一个候选筛选的教学例子

假设抓取生成器给出三个候选 A、B、C，以下结果完全是教学设定：

| 候选 | IK | 预抓取连接 / 接近 | 附着后搬运 | 能否组成完整解 |
| --- | --- | --- | --- | --- |
| A | 成功 | 失败：接近被桌沿挡住 | 尚无必要继续 | 否 |
| B | 成功 | 成功 | 失败：携带物体不能通过 | 否 |
| C | 成功 | 成功 | 成功，后续放置释放也可行 | 是 |

三个 IK 解不等于三条任务解。增加 IK 候选可能改善后续连接机会，但不会保证任务有解；评价候选时必须保留其对应的场景与附着关系。

## 5. 属性从哪里来？

完整抓放源码设置任务属性：

```cpp
task.setProperty("group", "panda_arm");
task.setProperty("eef", "hand");
task.setProperty("ik_frame", "panda_hand");
```

它们分别说明主规划组、末端名称和相关 IK 工作坐标。名称与模型的关系见[第二章](../02_moveit_setup/README.md)。

对子容器，代码又显式使用：

```cpp
task.properties().exposeTo(grasp->properties(), {"eef", "group", "ik_frame"});
grasp->properties().configureInitFrom(
    mtc::Stage::PARENT, {"eef", "group", "ik_frame"});
```

| 方式 | 本例中的意思 |
| --- | --- |
| `setProperty` / `setGroup` 等 setter | 直接给当前任务或阶段设置值 |
| `exposeTo` | 向另一个属性表声明所需属性及相关类型等信息；不能独自当作全部值已自动传递 |
| `configureInitFrom(PARENT, ...)` | 声明从父级属性初始化指定字段 |
| `configureInitFrom(INTERFACE, {"target_pose"})` | 从输入接口状态取得候选目标位姿 |

手爪开合阶段显式 `setGroup("hand")`，不能继承手臂组后就假定会自动识别为手爪运动。抓取 `ComputeIK` 从父级获得 `eef`、`group`，从接口获得 `target_pose`：前者是任务上下文，后者随候选变化。

MTC 属性属于任务内部的数据系统，不是 ROS 节点参数，也不是所有子阶段共享一个可随意修改的全局字典。属性传播用法可对照 [MTC 属性说明](https://moveit.github.io/moveit_task_constructor/tutorials/properties.html)；其中不同语言示例只用于理解机制，本仓库接口按 Humble C++ 源码核对。

### 监视阶段有什么用？

本地抓取生成器监视 `current_state_ptr`；放置生成器监视 `attach_object_stage`。后一处需要知道选定抓取之后物体相对手爪的关系，不能只拿最初桌面上物体的位姿当作携物状态。

`setMonitoredStage()` 监听的是该阶段生成的规划解及场景信息，不是实时摄像头监控，也不证明真实物体被抓住。保留 Stage 指针用于引用，与“操作系统线程监视器”没有关系。

## 6. 例子三：方向向量与距离范围怎样读？

完整抓放源码中的相对运动包括：

| 阶段 | 方向参考系与向量 | 平移距离范围 |
| --- | --- | --- |
| `approach object` | `panda_hand` 下 `(0,0,1)` | `0.1～0.15 m` |
| `lift object` | `world` 下 `(0,0,1)` | `0.1～0.3 m` |
| `retreat` | `world` 下 `(-0.5,0,0)` | `0.1～0.3 m` |

**解释：** 接近沿手爪局部 `+Z`，抬升沿世界 `+Z`；手爪旋转后，这两个方向一般不同。撤离向量的 `-0.5` 在这个设有距离范围的调用中用于给出 `-X` 方向，不能解释为“撤离速度是 0.5 m/s”或“固定退 0.5 m”。

在纯平移且设有正最大距离时，Humble `MoveRelative` 会按方向和距离构造目标，并以最小距离等条件判断返回段是否可接受，参见 [对应实现](https://raw.githubusercontent.com/moveit/moveit_task_constructor/humble/core/src/stages/move_relative.cpp)。实际达到多少仍看阶段输出，不能把范围上界当成实测位移。

抓取采样步长 `π/12 rad = 15°` 是候选方向的角度间隔；`setMaxIKSolutions(8)` 是每个相应 IK 求解设置的候选数量限制，不是八次成功抓取，也不是最终一定得到八条任务解。

## 7. 初始化、规划、发布与执行分别检查什么？

本地几个 MTC 程序的核心流程可概括为：

```text
createTask()
    → init()：捕获 InitStageException
    → plan(5)：检查规划返回值
    → solutions().front()：选取已有解
    → publishSolution(...)：发布可视化
    → execute(...)：检查 MoveIt 错误码
```

- **初始化失败：** 优先检查阶段连接方式、属性、组名和求解器等；初始化通过不证明几何问题可行。
- **规划失败：** 检查哪个阶段没有产生可用候选，或哪些候选无法连接。单看顶层 “Task planning failed” 不够定位。
- **`plan(5)`：** 参数用于限制规划搜索的解数量目标，不是“只进行五次内部尝试”，也不是执行五遍；可能由于其他停止条件只得到较少解。签名见 [Humble Task 接口](https://raw.githubusercontent.com/moveit/moveit_task_constructor/humble/core/include/moveit/task_constructor/task.h)。
- **解的选择：** 解集合按代价组织，`front()` 用于选择其前面的解。代价由阶段与任务的 cost term 决定，不自动等于真实成功率或最短执行时间；失败时不能对空集合取首元素。
- **执行失败：** 已有任务解仍可能因控制器、状态变化或接口问题执行失败。当前案例检查了 MTC 执行返回码，但未因此获得物体接触或放置稳定性测量。

与直接 MoveGroupInterface 程序相比，MTC 执行还需要相应的任务解执行能力与服务端配置，不能假定只启动任务节点就齐备。具体集成可参见 [Humble MTC 抓放教程](https://moveit.picknik.ai/humble/doc/tutorials/pick_and_place_with_moveit_task_constructor/pick_and_place_with_moveit_task_constructor.html)。

## 8. 失败定位与源码阅读边界

| 症状 | 优先查哪一层 |
| --- | --- |
| 属性缺失或类型不符 | 当前阶段 setter、父容器初始化、接口属性来源 |
| 有位姿候选但没有 IK | 组名、工具偏移、姿态、关节限制和求解预算 |
| 有抓取 IK，但连接失败 | 预抓取状态、接近方向、当前状态和障碍 |
| 附着后才失败 | 物体碰撞几何、手物相对变换、携物路径 |
| 每段看起来有解，任务仍失败 | 是否属于同一条兼容的状态链，而非不同候选各成功一段 |
| 有完整解但执行失败 | MTC 执行服务、底层控制器、当前状态与规划起点 |
| 任务函数结束，程序不退出 | `spin()` 停止与线程退出顺序，不是继续等待规划 |

`mtc_node.cpp` 中先 `spin_thread->join()`，后 `rclcpp::shutdown()`。在没有外部停止信号或 executor 取消的普通路径上，线程可能仍停留在 `spin()`，导致主线程等待；这是静态阅读发现的生命周期问题，不是本次运行观测。源码中的注释同样要与真实调用对照，不能直接当作 API 定义。

## 源码与参考

建议按“入门两阶段 → 完整抓放的容器与候选 → 桌面案例的场景变化”阅读源码。参数含义和阶段结构已按本地文件与官方资料核对，未运行 MTC，也没有实际候选数、规划耗时或执行成功率记录。

[入门源码](../packages/mtc_tutorial/src/mtc_node.cpp) · [完整抓放源码](../packages/hello_moveit/src/pick_and_place.cpp) · [分层任务构建](../packages/mtc_advanced_demo/src/task_builder.cpp)

[上一章：规划场景](../04_planning_scene/README.md) · [下一章：抓放任务](../06_pick_place/README.md) · [返回 MoveIt 目录](../README.md)
