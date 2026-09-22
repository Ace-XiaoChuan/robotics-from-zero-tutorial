# 表格与结构化结果

本文行数：23行，预期阅读时长：1分钟

已生成：

- `dataloader_inspection.json`：训练/验证 DataLoader 首批形状、类型、像素范围与缩放、标签配对检查。

- `dataset_overview.json`：数据规模、软件版本、原始存储、ToTensor 结果、batch 张量与测试集边界。
- `class_distribution.csv`：官方训练部分中 0～9 各类的样本数和占比。
- `mnist_split_indices.json`：随机种子 42 的训练/验证索引，分别为 50,000 和 10,000 个，后续实验统一复用。
- `split_summary.json`：数据质量检查、划分无重叠与完整覆盖检查、训练/验证各类数量。

后续训练时再在此保存：

- `batch_inspection.json`：在现有数据检查基础上补充 logits 的 shape 与 dtype；
- `training_history.csv`：每个实验、每个 epoch、每个 split 的 loss、accuracy 和耗时；
- `experiment_summary.csv`：E01～E06 的唯一变量、最佳验证结果与结论；
- `final_test_metrics.json`：锁定配置后的一次最终评估；
- `final_predictions.csv`：样本索引、真实类别、预测类别和预测置信度；
- `reload_check.json`：权重加载前后的固定样本输出对照。

CSV 字段名保持稳定，指标要标明 split。JSON 中同时保留 experiment ID、随机种子、数据划分和软件版本，不只保存一个准确率数字。
