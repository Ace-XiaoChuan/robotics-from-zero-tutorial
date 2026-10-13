# 16 视觉语言模型：从图文匹配到看图回答

本文行数：80行，预期阅读时长：6分钟

<a id="developer-overview"></a>

## 开发者理解：把图像与语言放进同一个任务

**VLM（视觉语言模型）利用图像和文字的联系，完成匹配、描述、问答或特定定位任务。** 与固定类别的图片分类相比，语言可以描述希望识别或询问的内容；不同 VLM 的能力和输出形式仍有区别。

例如，“这张图更符合哪段描述”需要图文匹配分数；“桌上有什么”需要生成回答；“左边红杯在哪里”需要把文字对象对应到图像区域。能回答问题，不自动代表能输出准确的像素位置。

**例子（教学场景）：** 一张左红杯、右蓝杯的照片，加上“左边杯子什么颜色”的问题，生成式 VLM 可以尝试回答“红色”。如果需求改为抓取这个杯子，还需要确认目标区域、三维几何和机器人执行信息，不能把回答当成抓取指令。本专题没有运行真实模型。

**图文对齐**表示模型学到跨图像与语言的语义联系，像让“红杯”文字与相关图像表示可比较；它不是相机与机器人坐标系的标定。图片也必须真正作为视觉输入进入模型，文件名或文字描述不能替代图片内容。

**生成的答案仍是预测。** 模型可能认错关系、补出不可见的细节，或在目标模糊时选错对象。格式正确、回答流畅和匹配分数高，分别描述输出的某些特点，不能单独证明图像事实正确。

使用已有 VLM 是推理；为自己的相机或任务更新参数是适配或微调。改问题或给上下文例子通常只改变本次输入条件，不等于完成训练。模型是否够用，要结合真正需要的输出理解。

**按需进入：** [文字与上下文](01_tokens_attention.md#developer-overview) · [图文匹配](02_clip_alignment.md#developer-overview) · [看图回答](03_generative_vlm.md#developer-overview) · [训练与评估](04_training_evaluation.md#developer-overview) · [机器人与 VLA](05_robotics_vla.md#developer-overview)。

**VLM（Vision-Language Model，视觉语言模型）把视觉信息和语言联系起来，用于图文检索、开放词汇识别、看图描述与问答等任务。** 本专题按“尚未学过 VLM”的起点编写，在[20 章导航](../README.md)中归第 16 章；默认阅读即可，不需要安装环境、下载权重或训练模型。

## 速记要点

- VLM 是一类模型，既包括 CLIP 这样的图文匹配模型，也包括能生成回答的模型；“VLM”不自动表示聊天模型。
- LLM（Large Language Model，大语言模型）主要处理语言序列；生成式 VLM 要增加视觉输入及其与语言连接的机制。
- 图像通常先变成特征向量或视觉 token，再参与计算；模型并非直接把图片文件名当作视觉内容。
- 图文“对齐”表示学会跨模态的语义关系，与机器人坐标系标定不是一回事。
- 模型输出的是预测。回答流畅、格式正确或相似度高，都不能单独证明图像事实正确。
- VLM 可以帮助机器人解释任务、选择目标；从像素到米制位姿、从目标到可执行动作，仍需具体接口与验证。

## 一个贯穿全文的例子

**输入条件（教学场景，未调用真实模型）：** 一张桌面 RGB 照片，图像宽 640 像素、高 480 像素。照片左侧有红杯，右侧有蓝杯；仅有这张照片，没有深度、相机标定或机器人关节状态。

| 想解决的问题 | 输入 | 输出示意 | 输出含义 |
| --- | --- | --- | --- |
| 找最匹配的描述 | 图片 + “红杯”“蓝杯”“猫”的候选文字 | 三个相似度分数 | 比较给定候选，并非一段回答 |
| 说明画面 | 图片 + “桌上有什么？” | “桌上有一个红杯和一个蓝杯。” | 根据图像条件生成文字 |
| 按语言找目标 | 图片 + “左边的红杯在哪里？” | 一个像素框，或带标记区域 | 需要具有定位能力的模型，普通问答模型未必支持 |
| 真正抓取 | 图像、指令、机器人状态等 | 目标位姿、轨迹或动作 | 还需要几何、规划、控制，或专门训练的动作策略 |

**结果与解释：** 同一张图能支持多种任务，但它们的输出契约不同。“红杯在左边”不足以求出以机器人基座为参考的抓取位姿，文字答案也不是电机指令。

## 按疑问选择专题

| 开发者理解入口 | 解决的疑问 | 深入时查什么 |
| --- | --- | --- |
| [01 token、LLM 与注意力](01_tokens_attention.md#developer-overview) | 模型怎样表示文字？为什么能关联上下文？ | 玩具词表、下一 token、两项注意力手算 |
| [02 CLIP 与图文对齐](02_clip_alignment.md#developer-overview) | 图片和文字如何比较？零样本是什么意思？ | 二维向量、相似度矩阵、对比损失 |
| [03 生成式 VLM 的数据流](03_generative_vlm.md#developer-overview) | 如何让语言模型利用图像回答？ | patch、视觉编码器、连接器、生成过程 |
| [04 训练、推理与评估](04_training_evaluation.md#developer-overview) | 哪些参数在学？怎样判断真的看了图？ | 回答 loss、LoRA、换图对照、失败分析 |
| [05 接入机器人与 VLA 的区别](05_robotics_vla.md#developer-overview) | 语言理解怎样接到感知、规划和控制？ | 红杯定位、像素反投影、动作语义 |

先读本页的开发者理解，再选择与当前疑问有关的专题入口；无需按顺序读完五篇。概念生疏时，可回查 [06 神经网络](../06_pytorch_networks/README.md#developer-overview)和 [07 迁移学习](../07_transfer_learning/README.md#developer-overview)，具体计算仍留在各页后方。

系统概念与原理可回查：[13 序列与编码器—解码器](../13_sequence_models/README.md#developer-overview)、[14 注意力与 Transformer](../14_attention_transformer/README.md#developer-overview)、[15 表示学习与预训练](../15_representation_learning/README.md#developer-overview)。[12](../12_detection_segmentation/README.md#developer-overview)解释定位输出与指标，[09](../09_probability_uncertainty/README.md#developer-overview)解释概率校准。本专题也保留就地说明，不要求先读完这些章节。

## 原理与失败现象回查

| 阅读页 | 新增机制或失败例子 | 读完应能分清 |
| --- | --- | --- |
| [02 CLIP](02_clip_alignment.md#candidate-changes) | 删除候选、加入同义描述改变 softmax；整图特征与局部关系 | 相对排名、概率校准、区域定位 |
| [03 连接器](03_generative_vlm.md#query-resampling) | 分辨率与 token 数；用两个查询汇总四个视觉 token | 特征维度、序列长度、信息压缩 |
| [04 训练](04_training_evaluation.md#frozen-gradient) | 固定下游线性模块，梯度仍传回可训练连接器 | 冻结权重、停止梯度、实际更新 |
| [05 机器人](05_robotics_vla.md#counterfactual-grounding) | 左右换图、左右换指令的成对计分；答对颜色却框错对象 | 文字正确、定位正确、几何与执行正确 |

基础注意力的完整推导放在 14，基础对比目标放在 15，五篇正文只保留 VLM 所需的就地解释。下章 [17](../17_generative_models/README.md)解释生成多种结果与扩散；动作标签、模仿学习与闭环偏移见 [18](../18_imitation_learning/README.md)。

这条预习分支可以现在开始，不以完成 S8 数据采集或 S9 行为克隆为前提；真正实现机器人动作策略时，再遵循[学习路线](../../../doc/learning-roadmap.md#s9)。VLA 在这里用于厘清概念，不展开完整策略训练课程。

## 数值例子与资料

专题使用 CLIP、LLaVA、BLIP-2 等代表结构解释图文模型。问答场景为教学示意，小向量例子展示具体计算，原论文与官方资料在相关解释旁链接。

[标准库数值例子](examples/README.md)核对图文匹配、注意力和梯度计算，更多例子见 [12～17](../examples/README.md#multimodal)。

[上一章：表示学习](../15_representation_learning/README.md) · [文字与上下文](01_tokens_attention.md#developer-overview) · [下一章：生成与扩散](../17_generative_models/README.md) · [机器学习目录](../README.md)
