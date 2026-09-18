# 总体目录与案例索引

本文行数：175行，预期阅读时长：8分钟

`lesson1`～`lesson9` 记录已有练习的编号。学习顺序由 [学习路线](../doc/learning-roadmap.md) 决定；同一个案例可以服务于多个阶段，查到需要的部分即可，不必每次从头运行整个案例。

**总体安排：以本仓库作为统一学习入口，按机器人知识主题组织；MuJoCo、MoveIt 与机器学习的现有运行代码继续保留在各自工作区。** 下方目录树是整理目标，不表示所有章节已经编写或运行通过。

[目标目录](#target-layout) · [MuJoCo、MoveIt 与机器学习如何接入](#integration) · [当前实际位置](#current-layout)

## 按主题查找已有内容

| 主题与路线阶段 | 已有入口 | 内容与边界 |
| --- | --- | --- |
| 工程基础，S0 | [单元索引](foundations/engineering/README.md) · [01 路径与环境](foundations/engineering/01_shell_paths/README.md) · [02 Git 协作](foundations/engineering/02_git/README.md) · [03 Python 与数值数据](foundations/engineering/03_python_numeric/README.md) | 单元 01～06 已有复习材料；代码验证范围见各单元 |
| 空间数学，S1 | [向量与矩阵](foundations/spatial_math/README.md) · [Lesson 3](lesson3/lesson3.py) | 基础章节用距离、投影和旋转轴复习基础运算；Lesson 3 为旋转与点变换代码 |
| ROS 2 基础通信，S2 | [Lesson 1](lesson1/README.md) · [接口笔记](lesson1/ros2_interfaces_notes.md) | 四节点通信，已整理详细文档；接口依赖和运行问题见本课记录 |
| ROS 2 执行与组合，S2 扩展 | [Lesson 2](lesson2/lesson2_composition/) | 同进程节点、Executor 与进程内通信练习；需补课程入口与构建验证 |
| 模型与仿真，S3 | [仿真目录](simulation/README.md) · [MuJoCo 材料](simulation/mujoco/materials.md) · [Lesson 7](lesson7/README.md) | 本地 Panda 加载、步进、Viewer 与外加关节力控制已有脚本；仅核对源码，控制效果未验证 |
| 正运动学，S4 | [Lesson 4](lesson4/lesson4_Modified_D-H.py) | Modified DH 的 2R 例子与几何验算 |
| FK / IK 与模型对齐，S4 | [Lesson 9 FK 检查](lesson9/check_fk_with_mujoco.py) · [雅可比笔记](lesson9/qpos_jacobian_notes.md) · [位姿误差笔记](lesson9/lie_group_lie_algebra_notes.md) | 已有脚本和解释，模型路径、坐标约定与数值结果待复核 |
| 控制与轨迹，S5 | [Lesson 7 轨迹跟踪](lesson7/joint_space_trajectory_tracking_demo.py) · [Lesson 9 末端控制](lesson9/control_ee_with_pinocchio.py) · [里程碑脚本](lesson9/kinematics_milestone.py) | 关节目标与末端控制练习；需分别标注直接设置状态和执行器控制的验证范围 |
| 视觉与状态估计，S6 | [Lesson 8](lesson8/README.md) · [详细笔记](lesson8/cv_trainning/README.md) | 相机、标定、AprilTag、PnP、传感器；外部资源依赖见笔记 |
| 规划与操作，S7 | [Lesson 5](lesson5/draw_line_and_circle.cpp) · [Lesson 6](lesson6/README.md) · `~/moveit-from-zero-tutorial` | MoveIt 路径与 MTC 抓取放置练习；独立 MoveIt 工作区保留完整构建资料，主仓库记录主题和验收边界 |
| 数据采集，S8 | [Lesson 8 episode 示例](lesson8/cv_trainning/demo/sim_camera_tag_pose_demo.py) | 已有 `.npz` 保存示例；时间对齐、动作语义与回放验证仍需检查 |
| 机器学习与模仿学习，S9 | [路线中的具体任务](../doc/learning-roadmap.md#s9) · `~/machine_learning_project` | 保存了 KNN、回归、决策树/模型选择、聚类和 PyTorch/迁移学习探索；与机器人数据和策略评估的连接仍需单独验证 |

以上是文件清点和归类，不是对代码正确性、可运行性或个人掌握程度的背书。

<a id="target-layout"></a>

## 预想的总体目录

主题目录按知识领域命名，内部统一用 `01_英文主题/README.md`，与 engineering 一致。编号只表示该主题内的阅读顺序；S0～S9 仍由学习路线维护，不写入目录名。

下面是**目标架构**。`[已有]` 仅表示当前主仓库已存在；其余为待整理章节，可能已有旧 lesson 或外部源码可用。所有主题目录均有导航 `README.md`，图中省略重复项。

```text
robotics-from-zero-tutorial/
├── README.md                         # 总入口与学习主线
├── AGENTS.md                         # 协作与文档约定
├── doc/
│   ├── README.md                     # 按问题查阅的知识索引
│   ├── learning-roadmap.md           # 学习顺序与先修关系
│   └── lesson-template.md            # 复习笔记样板
├── scripts/                          # 文档维护等工具
└── src/
    ├── README.md                     # 本页：总体架构与材料归属
    ├── foundations/
    │   ├── engineering/              # S0 [已有]
    │   │   ├── 01_shell_paths/
    │   │   ├── 02_git/
    │   │   ├── 03_python_numeric/
    │   │   ├── 04_cpp_build/
    │   │   ├── 05_debugging/
    │   │   └── 06_reproducibility/
    │   └── spatial_math/             # S1 [已有 01～04]
    │       ├── 01_vectors/
    │       ├── 02_dot_product/
    │       ├── 03_matrix_product/
    │       ├── 04_cross_product/
    │       ├── 05_frames_basis/
    │       ├── 06_rigid_transforms/
    │       ├── 07_rotation_representations/
    │       ├── 08_configuration_spaces/
    │       └── 09_derivatives_linearization/
    ├── ros2/                         # S2：程序间如何协作
    │   ├── 01_nodes_interfaces/
    │   ├── 02_parameters_launch/
    │   ├── 03_qos_executors/
    │   ├── 04_tf_time/
    │   └── 05_recording_debugging/
    ├── simulation/                   # S3 [已有导航]：机器人模型与仿真
    │   ├── 01_robot_models/          # 待写：通用模型概念、URDF / MJCF
    │   └── mujoco/                   # [已有索引] 对应 mujoco_workspace
    │       ├── materials.md          # [已有] 源码清点与主题归属
    │       ├── 01_model_loading/     # 以下为待写章节
    │       ├── 02_state_step/
    │       ├── 03_control_inputs/
    │       ├── 04_viewer_rendering/
    │       └── 05_reset_recording/
    ├── kinematics/                   # S4：关节与末端位姿
    │   ├── 01_planar_fk/
    │   ├── 02_dh_conventions/
    │   ├── 03_model_alignment/
    │   ├── 04_jacobian/
    │   └── 05_inverse_kinematics/
    ├── control/                      # S5：动力学与运动控制
    │   ├── 01_dynamics/
    │   ├── 02_pid_discrete_control/
    │   ├── 03_trajectory_generation/
    │   └── 04_joint_task_control/
    ├── perception/                   # S6：测量与机器人坐标对齐
    │   ├── 01_camera_calibration/
    │   ├── 02_tag_pose/
    │   ├── 03_frame_alignment/
    │   └── 04_state_estimation/
    ├── manipulation/                 # S7：规划与操作，包含 MoveIt
    │   ├── 01_motion_planning/
    │   ├── 02_moveit_setup/
    │   ├── 03_move_group_interface/
    │   ├── 04_planning_scene/
    │   ├── 05_mtc_stages/
    │   └── 06_pick_place/
    ├── machine_learning/             # 通用机器学习，S9 的先修分支
    │   ├── 01_supervised_knn/
    │   ├── 02_regression/
    │   ├── 03_preprocessing_pipeline/
    │   ├── 04_model_selection/
    │   ├── 05_clustering/
    │   ├── 06_pytorch_networks/
    │   └── 07_transfer_learning/
    ├── data_collection/              # S8：机器人示教与数据
    │   ├── 01_observation_action/
    │   ├── 02_time_alignment/
    │   ├── 03_demonstrations/
    │   └── 04_episode_replay/
    ├── robot_learning/               # S9：从数据学机器人策略
    │   ├── 01_behavior_cloning/
    │   ├── 02_rollout_evaluation/
    │   ├── 03_visual_policies/
    │   └── 04_advanced_policies/      # 按需：ACT、Diffusion Policy 等
    └── lesson1/ … lesson9/           # [已有] 整理期间保留的旧案例
```

工程基础按需查，机器人主线按 S1～S8 推进。通用机器学习可在掌握 Python 数值处理后穿插学习；进入机器人策略学习前，需要数据采集与回放、监督学习和基本神经网络知识。聚类、迁移学习和高级策略按需学习，不要求完成全部机器学习章节才能继续机器人主线。

<a id="integration"></a>

## MuJoCo、MoveIt 与机器学习如何接入

| 部分 | 在总体目录中负责什么 | 当前代码来源 |
| --- | --- | --- |
| `simulation/mujoco/` | 加载模型、读取状态、步进、控制输入、Viewer 与重置记录 | `~/mujoco_workspace/run_sim.py` 与 Menagerie Panda 场景；Lesson 7 / 8 / 9 补充相关材料 |
| `manipulation/` | 先理解规划、碰撞与执行，再讲 MoveIt 配置、接口、场景和 MTC 抓放 | Lesson 5 / 6；外部工作区的 `hello_moveit`、`mtc_tutorial`、`mtc_advanced_demo`、`panda_moveit_config` |
| `machine_learning/` | 分类、回归、预处理、模型选择、聚类、神经网络与迁移学习 | 外部 `projects/week01_iris_knn` 至 `week07_transfer_learning` 七个项目，按上表目标章节对应整理 |
| `data_collection/` | 定义 observation / action、时间对齐、示教和 episode 回放 | Lesson 8 的保存代码作为起点；完整数据链仍待整理 |
| `robot_learning/` | 将监督学习用于机器人动作预测，再用闭环执行评估策略 | 新增机器人任务适配；已有分类模型不能直接视为机器人策略 |

这些部分的衔接是：**MuJoCo 提供模型、状态与动力学仿真 → 规划与控制提供可执行任务和示教来源 → 数据采集保存状态与动作 → 机器学习提供训练方法 → 机器人学习评估策略执行效果。** 视觉网络也可服务于感知，不必都用于端到端动作预测。当前没有据此确认 MoveIt 与 MuJoCo 已打通，后续需要单独对齐模型、关节顺序、控制接口和时间。

MuJoCo 的工具接口放在 `simulation/mujoco/`，控制算法、感知和采集原理分别放回对应主题。MoveIt 的笔记放在 `manipulation/`，模型原理引用 `simulation/`，IK 原理引用 `kinematics/`，轨迹跟踪引用 `control/`，避免每章重复讲基础。通用机器学习同样只保留一份主要解释，机器人学习章节侧重动作语义、数据划分和闭环误差。

<a id="current-layout"></a>

## 当前实际位置与整理方式

截至 2026-09-18，主仓库已建立 `foundations/engineering/` 六章、`foundations/spatial_math/` 四章，以及 `lesson1`～`lesson9` 的已有材料。本次新增 `simulation/`、`simulation/mujoco/` 导航与材料清点；具体 MuJoCo 章节和其余主题目录尚未建立。

```text
~/robotics-from-zero-tutorial/        # 学习总入口、机器人笔记与案例
~/mujoco_workspace/                  # MuJoCo 局部探索，保留原位置
│   run_sim.py                      # Panda 仿真与控制脚本
│   mujoco_menagerie/               # 模型库
│   mj_env/、MUJOCO_LOG.TXT         # 本地环境与日志
│   task.md                         # 旧计划，仅作历史参考
~/moveit-from-zero-tutorial/          # 独立 ROS 2 工作区
│   src/                             # 教程包、配置和 MoveIt 等依赖源码
│   build/、install/、log/           # 本机构建产物
~/machine_learning_project/          # 独立机器学习项目
    projects/week01_… ～ week07_…    # 已有项目
    requirements.txt                # 依赖说明
```

**统一的是知识目录，运行环境继续按项目管理。** 主仓库的 MuJoCo、MoveIt 与机器学习章节保存简洁复习笔记、结果解释和源码定位；现有完整程序留在原工作区，避免复制依赖源码、模型权重和构建目录。外部位置当前按同一主目录下的兄弟项目约定记录；章节落地时补仓库来源与版本，不能仅凭本机路径宣称别人可复现。

迁移与编写按以下约定进行：

- 每个主题的 `README.md` 只放章节导航；每章用“速记 → 例子 → 结果与解释”，不设置读者必做的实验和验收章节。
- 有实际内容才建目录；章节代码很少时直接内嵌，较多时放旁边的脚本或 `examples/`。ROS 包保持自己的构建结构，不受笔记章节编号约束。
- Lesson 1 / 2 对应 ROS 2；Lesson 3 对应空间数学；Lesson 4 / 9 对应运动学；Lesson 7 拆到仿真与控制；Lesson 8 拆到感知与数据采集；Lesson 5 / 6 对应规划与操作。
- 旧 lesson 整理一部分就更新一部分引用；迁移时保留有效笔记和失败记录，并检查路径、导入、模型与构建入口。跨主题内容用链接复用。
- 本页维护目录目标，[学习路线](../doc/learning-roadmap.md)维护先修与推进顺序，[知识索引](../doc/README.md)维护已写章节的检索入口；未编写的规划路径不做成可点击链接。

返回 [知识索引](../doc/README.md) · [仓库首页](../README.md)。
