# 教程与源码总目录

本文行数：102行，预期阅读时长：4分钟

教程和源码按主题集中保存；目录树只列实际存在的内容。每个主题从 README 进入，先看速记、例子与结果解释，需要时查源码。未配齐环境不影响阅读。

## 按主题查找

| 主题 | 阅读入口 | 源码组织 |
| --- | --- | --- |
| 工程基础 S0 | [工程基础](foundations/engineering/README.md) | 六个复习单元 |
| 空间数学与数值方法 S1 | [十章复习目录](foundations/spatial_math/README.md) | 向量、旋转与变换、位姿误差、最小二乘、伪逆与约束优化；含数值检查及历史案例 |
| ROS 2 S2 | [通信与系统](ros2/README.md) | 五章笔记；examples/communication 与 composition |
| 模型仿真 S3 | [模型与 MuJoCo](simulation/README.md) | 七章笔记，先看控制流与轨迹时间；含自带模型、数值检查及历史案例 |
| 运动学 S4 | [八章复习目录](kinematics/README.md) | FK、DH、模型对齐、Jacobian、IK、奇异性、冗余与工作空间；含数值检查及历史案例 |
| 动力学、轨迹与控制 S5 | [章节目录与已有材料](control/README.md) | 面向动力学初学者的七部分目录，01～06 基础概念至控制与约束已补齐，07 待编写；保留仿真和运动学参考案例 |
| 感知与估计 S6 | [六章复习目录](perception/README.md) | 成像标定、目标位姿、噪声、误差传播、Kalman 与时间对齐；含数值检查及旧视觉案例 |
| 规划操作 S7 | [MoveIt / MTC](manipulation/README.md) | 六章 MoveIt / MTC 与五个规划原理专题；packages 内保存六个 ROS 包 |
| 数据采集 S8 | [数据采集](data_collection/README.md) | 复用视觉采集代码 |
| 机器学习 | [20 章导航与已有材料](machine_learning/README.md) | 01～20 正文已深化或补齐，16 保留五篇 VLM 正文并补齐衔接；真实模型与机器人验证单独记录 |

机器人策略学习仍是 [路线 S9](../doc/learning-roadmap.md#s9) 中的扩展方向，尚无完整案例，不创建空目录。

<a id="target-layout"></a>
<a id="current-layout"></a>

## 实际目录

```text
src/
├── foundations/
│   ├── engineering/                    # 六章工程复习
│   └── spatial_math/                   # 十章复习、数值检查及 examples/rigid_transforms
├── ros2/                               # 五章 + examples/communication、composition
├── simulation/
│   ├── 00_control_flow/                 # 导读：轨迹时间、仿真与真机控制流
│   ├── 01_robot_models/
│   └── mujoco/                         # 五章、models、examples/state_and_control、legacy
├── kinematics/
│   ├── 01_forward_kinematics/
│   ├── 02_dh_conventions/
│   ├── 03_model_alignment/
│   ├── 04_jacobian/
│   ├── 05_inverse_kinematics/
│   ├── 06_singularities/
│   ├── 07_redundancy/
│   ├── 08_workspace_limits/
│   └── examples/model_alignment/
├── control/                            # 动力学、轨迹与控制：零基础 01～06 入门正文、07 规划与参考材料
├── perception/examples/camera_and_tags/
├── manipulation/
│   ├── 01_motion_planning/
│   ├── 02_moveit_setup/
│   ├── 03_move_group_interface/
│   ├── 04_planning_scene/
│   ├── 05_mtc_stages/
│   ├── 06_pick_place/
│   ├── 07_configuration_space/
│   ├── 08_collision_checking/
│   ├── 09_sampling_planning/
│   ├── 10_constrained_planning/
│   ├── 11_trajectory_optimization/
│   └── packages/                       # 完整 ROS 包，不按章节拆散
├── data_collection/                    # 已有采集代码索引
├── machine_learning/
│   ├── README.md                       # 20 章导航与已有材料
│   ├── 机器学习入门实战清单.md           # 20 章正文建设工作项已完成
│   ├── 01_supervised_knn/
│   ├── 02_regression/
│   ├── 03_preprocessing_pipeline/
│   ├── 04_model_selection/
│   ├── 05_clustering/
│   ├── 06_pytorch_networks/
│   ├── 07_transfer_learning/
│   ├── 08_robot_integration/            # 机器人接口与任务结果；闭环未验证
│   ├── 09_probability_uncertainty/      # 概率、位置统计、校准与不确定性
│   ├── 10_classical_models/             # 逻辑回归、SVM、树与集成的四点比较
│   ├── 11_training_optimization/        # 训练机制、优化更新与人工曲线
│   ├── 12_detection_segmentation/      # 分类、框、掩码、关键点与评价
│   ├── 13_sequence_models/             # 时间历史、RNN/GRU 与编码器—解码器
│   ├── 14_attention_transformer/        # 注意力、Transformer、token 与缓存
│   ├── 15_representation_learning/     # 重建、对比、掩码与预训练
│   ├── 16_vision_language/              # VLM 五篇正文，已深化并衔接基础
│   ├── 17_generative_models/           # 多解、绕障示意与扩散公式
│   ├── 18_imitation_learning/           # 动作标签、BC、DAgger、ACT 与 Diffusion Policy
│   ├── 19_reinforcement_learning/       # 回报、价值、Q 更新、策略梯度与 PPO/SAC
│   ├── 20_generalization_sim2real/      # 独立评价、随机化、延迟、约束与恢复
│   └── examples/                       # 01～20 标准库教学数值与机制核对
└── lesson1/ … lesson9/                 # 仅保留历史编号跳转 README
```

<a id="integration"></a>

## 维护约定

- 新笔记和源码直接进入所属主题；旧 lesson 路径只用于找回原案例位置。
- 完整案例的导入、模型配置、ROS 包结构一起保留；跨主题通过链接复用，同一实现不保存多份。
- 章节编号表示主题内顺序，不代表未创建的编号必须补齐。后续计划写在学习路线，不画成已存在目录。
- 只保留教程、自有源码、小型配置与必要历史结果，运行环境和大型资源不打包。
- 文件迁移和静态检查不代表构建、训练或控制验证通过，也不代表个人学习验收。

[迁移对照与检查范围](../doc/directory-reorganization.md) · [知识索引](../doc/README.md) · [学习路线](../doc/learning-roadmap.md) · [首页](../README.md)
