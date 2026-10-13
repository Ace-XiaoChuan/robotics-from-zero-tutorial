# 机器学习：按功能查阅的 20 章知识库

本文行数：60行，预期阅读时长：4分钟

机器学习让程序从数据中学习预测或决策方法。这里按 20 章整理，从分类、回归和神经网络，延伸到视觉语言模型与机器人学习。各章先用“开发者理解”说明用途和输入输出，再提供例子、推导与实现。

## 怎样阅读

有具体需求时，直接从下表找到相关概念入口；想先串起任务和方法，可读[概念总览的开发者理解](overview.md#developer-overview)。章节编号用于导航，不要求按编号重学。

概念模糊时，再读原有“速记要点”和例子；想解释计算、排查异常或修改实现时，再进入正文推导、源码与参考笔记。

## 20 章导航

| 章节 | 开发者理解入口 | 这章帮助理解什么 |
| --- | --- | --- |
| 01 | [监督学习与 KNN](01_supervised_knn/README.md#developer-overview) | 利用带答案的例子预测新输入 |
| 02 | [回归、损失与正则化](02_regression/README.md#developer-overview) | 数值预测、误差和模型复杂度 |
| 03 | [预处理与评估指标](03_preprocessing_pipeline/README.md#developer-overview) | 完整预测流程、漏报与误报 |
| 04 | [泛化与模型选择](04_model_selection/README.md#developer-overview) | 对新数据是否有用，怎样比较方案 |
| 05 | [聚类与降维](05_clustering/README.md#developer-overview) | 相似分组、压缩表示和信息损失 |
| 06 | [神经网络与反向传播](06_pytorch_networks/README.md#developer-overview) | 可训练的预测功能，训练与推理的区别 |
| 07 | [CNN 与迁移学习](07_transfer_learning/README.md#developer-overview) | 利用已有视觉能力适配自己的任务 |
| 08 | [与机器人结合](08_robot_integration/README.md#developer-overview) | 从模型输出到定位、规划、执行与反馈 |
| 09 | [概率与不确定性](09_probability_uncertainty/README.md#developer-overview) | 分数、可靠程度和估计误差 |
| 10 | [经典模型与方法选择](10_classical_models/README.md#developer-overview) | 用不同预测规则实现同一功能 |
| 11 | [训练优化与失败现象](11_training_optimization/README.md#developer-overview) | 训练能否改善，以及改善了什么 |
| 12 | [检测、分割与关键点](12_detection_segmentation/README.md#developer-overview) | 类别、区域、轮廓和指定点的区别 |
| 13 | [序列模型](13_sequence_models/README.md#developer-overview) | 需要历史与顺序的预测 |
| 14 | [注意力与 Transformer](14_attention_transformer/README.md#developer-overview) | 上下文、信息联系与逐步生成 |
| 15 | [表示学习与预训练](15_representation_learning/README.md#developer-overview) | 可复用特征与自监督目标 |
| 16 | [视觉语言模型 VLM](16_vision_language/README.md#developer-overview) | 图片与文字共同参与任务 |
| 17 | [生成与扩散模型](17_generative_models/README.md#developer-overview) | 同一条件下产生多个合理候选 |
| 18 | [模仿学习与动作策略](18_imitation_learning/README.md#developer-overview) | 从示教学习连续动作 |
| 19 | [强化学习](19_reinforcement_learning/README.md#developer-overview) | 通过环境交互与奖励学习行为 |
| 20 | [泛化与仿真迁移](20_generalization_sim2real/README.md#developer-overview) | 换条件后的任务表现与证据范围 |

先修关系用于回查原理，实际机器人开发仍按[学习路线](../../doc/learning-roadmap.md)安排数据、模型和闭环任务。

## VLM 按疑问进入

| 开发者理解入口 | 先建立什么认识 |
| --- | --- |
| [01 文字与上下文](16_vision_language/01_tokens_attention.md#developer-overview) | token、顺序、上下文与生成 |
| [02 图文匹配](16_vision_language/02_clip_alignment.md#developer-overview) | 候选描述、相似度与检索 |
| [03 看图回答](16_vision_language/03_generative_vlm.md#developer-overview) | 图片成为回答依据，视觉与语言怎样衔接 |
| [04 训练与评估](16_vision_language/04_training_evaluation.md#developer-overview) | 改输入、适配能力和确认事实效果 |
| [05 机器人与 VLA](16_vision_language/05_robotics_vla.md#developer-overview) | 语言选目标与模型输出动作的区别 |

只读与当前问题有关的专题即可；序列、注意力和表示学习在 13～15 保留系统回查，不要求先读完它们才能理解 VLM 用途。

## 源码与结果

01～07 的 `src/` 保存训练与数据处理程序，`reference.md` 解释实现流程；02～07 的 `results.md` 保存实验配置和指标，01 的结果保存在 `outputs/knn_results.json`。07 的 `concepts.md` 详细解释 CNN 与迁移学习，各章 `outputs/` 收录小型图表和指标文件。

[教学数值程序](examples/README.md)用于核对公式与小模型；[合成回归与学习曲线](02_regression/examples/capacity/README.md)展示模型复杂度、正则化和数据量的影响。

运行训练代码时，按各章数据说明准备数据集与权重，依赖见 [requirements.txt](requirements.txt)。机器人观测、动作和任务执行见 [08](08_robot_integration/README.md)，数据采集与策略开发见[学习路线 S8 / S9](../../doc/learning-roadmap.md#s8)。

[概念总览](overview.md) · [返回总索引](../README.md)
