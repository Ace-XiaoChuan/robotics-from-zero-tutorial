# 机器学习快速复习与源码

本文行数：25行，预期阅读时长：2分钟

七组教程、源码和已有解释集中保存在这里。先看各篇开头的“速记 → 例子 → 结果与解释”，需要推导或历史结果时再往下读。目录已改为 01～07 主题章节；用户已学过这些内容，不要求重做训练。

| 主题 | 复习笔记 | 实现 |
| --- | --- | --- |
| KNN 分类 | [01_supervised_knn](01_supervised_knn/README.md) | [源码](01_supervised_knn/src) |
| 回归 | [02_regression](02_regression/README.md) | [源码](02_regression/src) |
| 预处理与 Pipeline | [03_preprocessing_pipeline](03_preprocessing_pipeline/README.md) | [源码](03_preprocessing_pipeline/src) |
| 模型选择 | [04_model_selection](04_model_selection/README.md) | [源码](04_model_selection/src) |
| 聚类 | [05_clustering](05_clustering/README.md) | [源码](05_clustering/src) |
| PyTorch 神经网络 | [06_pytorch_networks](06_pytorch_networks/README.md) | [源码](06_pytorch_networks/src) |
| 迁移学习 | [07_transfer_learning](07_transfer_learning/README.md) | [源码](07_transfer_learning/src) |

## 保存范围与结果含义

- 保留 Python 源码、完整 Markdown 笔记、数据来源说明、原 requirements.txt，以及小型历史 JSON 指标和说明图。
- 不保存数据集、数据划分副本、模型权重、虚拟环境和逐样本预测表。文中的“已下载”“本次运行”指原项目记录，不能据此认定此仓库包含数据或已完成复测。
- 长篇原文中的命令是按需参考，当前目录使用 `src/machine_learning/01_… ～ 07_…`；运行需要自行提供对应依赖和数据。本次只检查迁入完整性、语法和文档路径，没有训练模型。
- 历史结果保留原来的条件和解释；它们不是读者必须达到的成绩，也不是对个人掌握程度的新判断。
- [原实战清单](机器学习入门实战清单.md) 作为历史材料；当前复习按本页主题索引，机器人策略应用见 [S9](../../doc/learning-roadmap.md#s9)。

[迁入范围与来源](../../doc/source-consolidation.md) · [返回总索引](../README.md)
