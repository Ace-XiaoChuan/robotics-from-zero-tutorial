# 图表产物

本文行数：17行，预期阅读时长：1分钟

已生成：

- `mnist_representative_samples.png`：官方训练部分中 0～9 各一张样例，标题保留真实标签和样本索引。
- `class_distribution.png`：官方训练部分中每个数字的样本占比；不查看测试标签分布。

后续训练时再在此保存：

- 每个实验的 train/validation loss 和 accuracy 曲线；
- E01～E06 受控对比图；
- 最终混淆矩阵；
- 至少 10 个带真实类别和预测类别的错误样本。

训练图表的标题必须标明数据 split 和 experiment ID，避免将验证结果误当成测试结果。
