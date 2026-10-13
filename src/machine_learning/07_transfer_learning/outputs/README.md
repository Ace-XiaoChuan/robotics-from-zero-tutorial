# 迁移学习图表与指标

本文行数：20行，预期阅读时长：1分钟

| 文件 | 内容 |
| --- | --- |
| [图片检查](tables/inspection_summary.json) | 类别、图片格式与张量示例 |
| [DataLoader](tables/dataloader_summary.json) | 预处理、批次形状与数量 |
| [模型摘要](tables/model_summary.json) | ResNet18 与三分类头的参数、输出形状 |
| [单批损失](tables/loss_summary.json) | 原始 logits、标签与交叉熵 |
| [单批更新](tables/train_step_summary.json) | 更新前后损失、梯度与参数变化 |
| [基线逐轮指标](runs/20260914_164706_687481/history.json) | 未增强版本的训练和验证结果 |
| [基线测试指标](runs/20260914_164706_687481/test_evaluation/test_metrics.json) | 固定测试集成绩 |
| [增强版逐轮指标](runs/20260921_augmented/history.json) | 增强版本的训练和验证结果 |
| [增强版测试指标](runs/20260921_augmented/test_evaluation/test_metrics.json) | 分类指标与混淆矩阵 |
| [增强版曲线](runs/20260921_augmented/training_curves.png) | 三轮训练和验证曲线 |

训练保存最佳权重 `best_model.pt`；评估生成预测表、混淆矩阵和错误图片。完整图片与权重需要运行时准备。

[实验结果](../results.md) · [本章入口](../README.md)
