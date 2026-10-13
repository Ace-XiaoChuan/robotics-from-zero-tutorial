# MNIST 图表与指标

本文行数：18行，预期阅读时长：1分钟

| 文件 | 内容 |
| --- | --- |
| [示例图片](figures/mnist_representative_samples.png) | 训练部分的 0～9 各一张图 |
| [类别分布](figures/class_distribution.png) | 训练部分的样本占比 |
| [数据概览](tables/dataset_overview.json) | 图片、标签和批次的形状、类型与值域 |
| [DataLoader 检查](tables/dataloader_inspection.json) | 批次形状、缩放和标签配对 |
| [划分摘要](tables/split_summary.json) | 训练 50,000、验证 10,000 的划分配置 |
| [E01 曲线](runs/E01_20260909_004120_002242/learning_curves.png) | 五轮训练与验证 loss、accuracy |
| [E01 配置](runs/E01_20260909_004120_002242/config.json) | 模型、超参数与软件版本 |
| [E01 摘要](runs/E01_20260909_004120_002242/summary.json) | 最佳验证成绩与权重加载检查 |

`train.py` 将每次训练保存在 `runs/实验ID_时间戳/`，生成配置、逐轮指标、曲线和权重。权重与完整数据在运行时准备。

[实验结果](../results.md) · [本章入口](../README.md)
