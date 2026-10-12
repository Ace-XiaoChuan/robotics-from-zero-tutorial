# 机器学习：20 章目录与已有材料

本文行数：70行，预期阅读时长：6分钟

机器学习按 20 章组织：保留原八章主题，再补统计与训练基础、视觉与序列模型、VLM、生成模型及机器人学习。第 08 章是“与机器人结合”，VLM 调整为第 16 章。具体小节、建设状态和 agent 待办统一维护在[20 章工作目录](机器学习入门实战清单.md)。

保持“速记要点 + 例子 + 结果与解释”，默认阅读即可；新概念在首次出现时说明，核心机制按需展开必要推导。已有入门内容用于快速复习，新增内容用于逐步加深理解，不要求重复训练或完成必做实验。

## 从哪里开始

先读[概念总览](overview.md)，串起“任务 → 学习信号 → 模型 → 训练与评估”。回顾 CNN 与迁移学习，可直接读 [07](07_transfer_learning/README.md)，其中解释了“只训练分类头，为什么已经在使用深度学习”。

当前需要 VLM 时，直接进入 [16 VLM](16_vision_language/README.md)：token 与注意力 → CLIP 图文对齐 → 生成式 VLM → 训练评估 → 机器人接口。它保留就地概念解释；[13 序列](13_sequence_models/README.md)、[14 注意力](14_attention_transformer/README.md)、[15 表示学习](15_representation_learning/README.md)已提供系统回查，不要求先重读。

## 20 章导航

01～20 均已提供可直接阅读的正文，基础章节已深化，VLM 保留五篇专题。材料状态不表示个人掌握或模型与机器人验收完成。

| 章节 | 阅读入口或规划 | 当前状态 |
| --- | --- | --- |
| 01 | [监督学习与 KNN](01_supervised_knn/README.md) | 已深化正文，源码与历史结果保留 |
| 02 | [回归、损失与正则化](02_regression/README.md) | 已深化，保留合成回归与新增手算例子 |
| 03 | [数据预处理与评估指标](03_preprocessing_pipeline/README.md) | 已深化正文，源码与历史结果保留 |
| 04 | [泛化、过拟合与模型选择](04_model_selection/README.md) | 已深化，保留学习曲线与新增误差分解 |
| 05 | [聚类与降维](05_clustering/README.md) | 已深化正文，源码与历史结果保留 |
| 06 | [神经网络与反向传播](06_pytorch_networks/README.md) | 已深化正文，源码与历史结果保留 |
| 07 | [CNN 与迁移学习](07_transfer_learning/README.md) | 已深化正文与 CNN 解释，源码保留 |
| 08 | [与机器人结合：从模型输出到任务执行](08_robot_integration/README.md) | 已有教程与候选筛选核对，闭环未验证 |
| 09 | [概率、统计与预测不确定性](09_probability_uncertainty/README.md) | 已提供正文与先验、校准、熵的数值核对 |
| 10 | [经典模型进阶与方法选择](10_classical_models/README.md) | 已提供正文与同组四点比较，真实模型未训练 |
| 11 | [深度网络为什么能训练、为什么会失败](11_training_optimization/README.md) | 已提供正文、优化数值与示意曲线，未运行新深度训练 |
| 12 | [从图像分类到检测、分割与关键点](12_detection_segmentation/README.md) | 已提供正文、同场景图示与区域/排名核对 |
| 13 | [序列模型与编码器—解码器](13_sequence_models/README.md) | 已提供正文、历史运动与递推梯度核对 |
| 14 | [注意力、Transformer 与语言模型](14_attention_transformer/README.md) | 已提供正文、遮罩/多头/单层缓存核对 |
| 15 | [表示学习、自监督与预训练](15_representation_learning/README.md) | 已提供正文、重建/对比/掩码例子核对 |
| 16 | [视觉语言模型 VLM](16_vision_language/README.md) | 五篇正文已深化并衔接 12～15，真实模型未运行 |
| 17 | [生成模型与扩散模型](17_generative_models/README.md) | 已提供正文、绕障图与扩散公式核对，未训练模型 |
| 18 | [模仿学习与机器人动作策略](18_imitation_learning/README.md) | 已有正文、BC 与反馈推导、块索引核对，未训练策略 |
| 19 | [强化学习：从回报到连续动作](19_reinforcement_learning/README.md) | 已有正文、价值更新与概率梯度核对，未训练 PPO/SAC |
| 20 | [机器人学习的泛化与仿真迁移](20_generalization_sim2real/README.md) | 已有正文、评估统计与扰动推导，未做实际迁移 |

章节编号用于导航，先修关系帮助回查知识；不必按顺序重读已熟悉的部分。01～20 正文建设工作已完成；实际任务仍按[学习路线](../../doc/learning-roadmap.md)核对数据、接口和评估。

## 笔记与源码怎么放

- 各章 `README.md`：当前复习正文；01～20 已按工作目录深化或补齐。
- 16 的 `README.md`：VLM 预习与深化入口；五篇正文逐步解释新概念，`examples/` 保存原有教学数值核对，不含真实模型推理或训练实现。
- 各章 `reference.md`：原长篇笔记、推导与运行步骤，保留当时语境；07 的 `concepts.md` 另保留 CNN 详细讲解。
- 各章 `src/`：已有实现；`experiment_log.md`、`outputs/`：保留的历史记录与小型结果。
- [20 章工作目录](机器学习入门实战清单.md)：各章编写范围、参考例子、建设状态与完成标准；原八周计划已被替代并清理。

## 结果与运行边界

“示意”表示为解释概念而选择的数字；“静态推导”表示按公式或源码计算；“历史记录”表示迁入的既往结果。原复习整理未重训历史模型；第 02、04 章新增合成回归已实际运行，见[核对记录](02_regression/examples/capacity/README.md)。不把文件存在当作个人掌握或历史实验复测的证据。

01～08 的[17 组教学数值与接口条件核对](examples/README.md)已通过，另重新运行合成回归的 7 项求解器检查。小网络梯度与数值差分一致；08 的几何与条件筛选不包含 ROS、规划控制或动力学抓取验证。

09～11 的 [20 组教学数值与解析解核对](examples/README.md#advanced)已通过，涵盖先验变化、位置方差、似然、熵、XOR 边界、核 SVM 最优性、提升负梯度、优化器状态与正则化。11 提供标明人工数据的曲线图；本轮未训练真实模型或进行 PyTorch 运行时对照。

第 16 章现有 VLM 预习材料通过 [8 组教学数值核对](16_vision_language/examples/README.md)；未加载、训练或评估真实 VLM/VLA，文字答案与机器人流程为教学示意或建议设计。

12～17 新增 [33 组教学数值与机制核对](examples/README.md#multimodal)，配有桌面视觉输出、绕障路径两张人工示意图。覆盖检测匹配、序列梯度、因果可见范围、缓存一致性、自监督目标、VLM 接口和扩散代数；采样例子的去噪器使用已知真噪声，不是训练成果。

18～20 新增 [26 组动作学习、回报与评估核对](examples/README.md#robot-learning)，配有理想误差递推图。覆盖 BC 解析解、误差累积、动作块、Bellman/Q 更新、策略梯度、PPO/SAC 目标、统计、延迟与限幅；未训练策略或运行机器人。四个共享程序共 96 组，原 VLM 另有 8 组教学检查。

数据集、权重、虚拟环境和部分生成产物未迁入。需要运行时，再查看各章数据说明、详细笔记及[依赖清单](requirements.txt)；历史绝对路径仅供追溯，不是本仓库的环境要求。

机器人方面，[概念总览](overview.md#robot-learning)先区分感知、行为克隆与强化学习；完整采集和策略任务仍按[学习路线 S8 / S9](../../doc/learning-roadmap.md#s8)推进。

[本次整理核对记录](verification.md) · [迁入来源](../../doc/source-consolidation.md) · [返回总索引](../README.md)
