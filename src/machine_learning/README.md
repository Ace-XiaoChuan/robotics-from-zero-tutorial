# 机器学习：按功能查阅的 20 章知识库

本文行数：104行，预期阅读时长：9分钟

机器学习让程序从数据中学习预测或决策方法。这里按 20 章整理，从分类、回归和神经网络，延伸到视觉语言模型与机器人学习。各章先用“开发者理解”说明用途和输入输出，再提供例子、推导与实现。

## 怎样阅读

有具体需求时，直接从 [20 章导航](#20-章导航)找到相关概念入口；想先串起任务和方法，可读[概念总览的开发者理解](overview.md#developer-overview)。章节编号用于导航，不要求按编号重学。

概念模糊时，再读原有“速记要点”和例子；想解释计算、排查异常或修改实现时，再进入正文推导、源码与参考笔记。

## 按模型理解与修改深度选择内容

以看懂处理流程、调整配置、向 AI 说清需求并指导修改为目标，可以按三个层级逐步深入。各层复用前一层的数据、接口和评估知识，根据当前任务选择阅读深度。

| 层级 | 能够完成的工作 | 主要章节 |
| --- | --- | --- |
| 1. 使用与部署 | 加载现成模型，处理自己的输入，解释输出，调整推理配置并检查效果 | 07 为主，补 03；检测任务加 12 |
| 2. 训练与微调 | 用自己的数据训练分类头或解冻部分网络，调整训练配置并选择模型 | 03、04、06、07，补 11 |
| 3. 修改模型与训练方法 | 更换或增删模块，改变信息流、损失或训练过程，并验证改动 | 06、07、11，按所修改的模型选读后续专题 |

深度取决于能解释和指导哪种修改。即使代码由 AI 编写，也需要说清修改位置、预期行为、输入输出约定和验收依据。

### 1. 使用与部署：把已有模型用于自己的输入

- **模型与推理：** 读 07 的[仓库任务：从照片到材料类别](07_transfer_learning/README.md#仓库任务从照片到材料类别)、[推理与微调的边界](07_transfer_learning/README.md#推理与微调的边界)，看懂图片、特征、类别分数与预测的关系。
- **输入与模型保存：** 读 07 概念笔记的 [§12 图片预处理](07_transfer_learning/concepts.md#12-图片预处理缩放裁剪与标准化)、[§14 标签与类别映射](07_transfer_learning/concepts.md#14-标签与类别映射为什么要保存)、[§15 Logits、概率与置信度](07_transfer_learning/concepts.md#15-logits概率与置信度)、[§19 保存与推理](07_transfer_learning/concepts.md#19-保存与推理怎样把训练结果真正用起来)。
- **评估与阈值：** 读 03 的[混淆矩阵](03_preprocessing_pipeline/README.md#例子二读懂混淆矩阵)、[类别不平衡](03_preprocessing_pipeline/README.md#类别不平衡99-准确率为什么仍可能没用)、[改变阈值](03_preprocessing_pipeline/README.md#同一批分数改变阈值会失去或得到什么)，能比较漏报、误报及阈值调整的代价。
- **检测任务按需补充：** 读 12 的 [§1 四种输出](12_detection_segmentation/README.md#1-同一张桌面图四种输出)、[§4 重复框、NMS 与 AP](12_detection_segmentation/README.md#4-重复框nms-与检测-ap)、[§6 关键点与坐标恢复](12_detection_segmentation/README.md#6-关键点与坐标恢复)，明确输出类型和缩放后的坐标怎样使用。

这一层读到能说明一次推理经过哪些步骤、训练时的预处理怎样恢复、结果怎样评估即可。阈值、输入尺寸等配置的调整，还要结合实际模型比较推理耗时和失败样本。

### 2. 训练与微调：用自己的数据适配模型

- **数据处理：** 读 03 的[验证数据怎样被悄悄用进去](03_preprocessing_pipeline/README.md#例子一验证数据怎样被悄悄用进去)、[标准化、填补与编码](03_preprocessing_pipeline/README.md#标准化填补与编码分别改变什么)，明确先划分数据，再拟合预处理。
- **模型选择：** 读 04 的[三种曲线](04_model_selection/README.md#三种曲线不要混淆)、[怎样走到模型选择](04_model_selection/README.md#怎样从教学比较走到模型选择)、[机器人数据按帧划分的问题](04_model_selection/README.md#机器人数据按帧分开为什么可能高估泛化)，明确配置比较和独立评估的依据。
- **训练流程：** 读 06 的[一次训练究竟发生什么](06_pytorch_networks/README.md#一次训练究竟发生什么)、[训练模式、评估模式与存储](06_pytorch_networks/README.md#训练模式评估模式与存储)，知道哪些步骤产生梯度、更新参数、评估和保存模型。
- **适配已有网络：** 读 07 的[冻结、微调与增强](07_transfer_learning/README.md#冻结微调与增强改变的是哪一部分)、[三轮训练与测试结果](07_transfer_learning/README.md#三轮训练与测试结果)，实现时对照[按轮训练、验证与最佳模型保存](07_transfer_learning/reference.md#按轮训练验证与最佳模型保存)。
- **调参与排查：** 读 11 的 [§2 学习率与输入尺度](11_training_optimization/README.md#2-学习率与输入尺度梯度大不等于应该迈大步)、[§7 看训练曲线](11_training_optimization/README.md#7-看训练曲线先判断现象再查原因)，先根据现象检查数据、更新链路和配置，再安排对照实验。

这一层需要能说明数据怎样划分、哪些参数允许更新、调节选项影响什么，以及怎样选择 checkpoint。前两层可以暂缓完整求导、卷积手算和优化器更新公式，保留对流程、配置和结果含义的理解。

### 3. 修改模型与训练方法：改变内部计算与学习目标

- **张量与损失：** 读 06 的[一张图怎样变成十个分数](06_pytorch_networks/README.md#仓库网络一张图怎样变成十个分数)、[分数、概率与损失](06_pytorch_networks/README.md#例子分数概率与损失)，能沿网络核对维度、标签格式和损失的输入。
- **模块与信息流：** 读 07 概念笔记的 [§7 特征提取部分和分类头](07_transfer_learning/concepts.md#7-特征提取部分和分类头)，区分替换输出头、改变特征提取模块和修改模块连接各自影响什么。
- **模块行为：** 涉及归一化或 Dropout 时，读 11 的 [§5 归一化](11_training_optimization/README.md#5-归一化输入统计与网络内统计)、[§6 Dropout 与训练、评估、求导](11_training_optimization/README.md#6-dropout-与训练评估求导的关系)，核对模式、统计量与梯度开关。
- **按改动深入：** 自定义损失或排查梯度时，再读 [06 反向传播推导](06_pytorch_networks/backpropagation.md)；涉及序列、注意力、生成或动作策略时，从下方 13～19 章导航选择对应专题。

这一层需要能解释改动后的输入输出、计算关系、损失鼓励的行为和参数更新范围，并用小例子核对实现，再比较任务效果。将三分类头换成五分类头与设计新的多分支损失，所需深入程度不同，数学推导按实际改动补充。

机器人应用可在任一层接入：[08](08_robot_integration/README.md)解释感知结果到定位、规划与执行的衔接，[20](20_generalization_sim2real/README.md)解释任务评估、延迟与失败恢复；准备让模型直接预测动作时，再读 [18](18_imitation_learning/README.md) 的观测、动作和闭环误差。坐标系、单位、关节顺序与时间含义需要随接口明确。

[05 聚类与降维](05_clustering/README.md)、[09 概率与不确定性](09_probability_uncertainty/README.md)作为按需专题：遇到分组、压缩、概率可靠性或估计误差问题时回查。表格数据应用也可从 [01 KNN](01_supervised_knn/README.md)、[02 回归](02_regression/README.md)、[10 方法选择](10_classical_models/README.md)进入，再按上述层级补数据、评估与修改知识。

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

[教学数值程序](examples/README.md)用于核对公式与小模型；[合成回归与学习曲线](02_regression/examples/capacity/README.md)展示模型复杂度、正则化和数据量的影响；[09 最小实践](09_probability_uncertainty/practice.md)用合成测量和独立分类标签展示统计估计、预测区间与概率校准，源码和图表保存在该章。

运行训练代码时，按各章数据说明准备数据集与权重，依赖见 [requirements.txt](requirements.txt)。机器人观测、动作和任务执行见 [08](08_robot_integration/README.md)，数据采集与策略开发见[学习路线 S8 / S9](../../doc/learning-roadmap.md#s8)。

[概念总览](overview.md) · [返回总索引](../README.md)
