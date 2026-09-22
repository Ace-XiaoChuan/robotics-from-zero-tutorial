# 第 6 周学习产物索引

本文行数：51行，预期阅读时长：2分钟

当前已实现数据准备与 E00/E01 基线训练。每次运行放在独立目录中，保留历史记录。

## 已完成：数据探索

| 产物 | 作用 |
| --- | --- |
| `figures/mnist_representative_samples.png` | 展示官方训练部分中 0～9 各一张示例图；它们是每类首个样本，不代表该类的唯一或典型写法 |
| `figures/class_distribution.png` | 比较官方训练部分中 0～9 的样本占比 |
| `tables/dataset_overview.json` | 记录原始数据、ToTensor 后单图和首个 batch 的 shape/dtype/值域 |
| `tables/class_distribution.csv` | 保留官方训练部分各类的精确数量和占比 |

## 模型与训练产物

每次训练在 `runs/实验ID_时间戳/` 保存：

- `config.json`：网络结构、输入处理、类别映射、超参数、软件版本与样本数。
- `batch_inspection.json`：输入、标签与 logits 形状，未训练时的一组输出分数。
- `history.csv`：每轮训练与验证 loss、accuracy 和耗时。
- `learning_curves.png`：训练与验证曲线。
- `best_state_dict.pt`：按验证准确率保存的最佳权重。
- `summary.json`：最佳轮次、验证成绩、耗时与权重加载检查。
- E00 另有 `smoke_indices.json`，记录小子集的原始索引。

下表是后续完整交付的规划。当前 E00/E01 的形状检查、曲线、配置、权重和加载结果集中在上述运行目录，具体运行链接见实验记录。

## 后续训练的最小交付集

| 计划产物 | 位置 | 用途 |
| --- | --- | --- |
| 带 logits 的 batch 形状检查 | `tables/batch_inspection.json` | 在当前数据检查基础上，补充模型输出 `[B, 10]` |
| 全部 epoch 记录 | `tables/training_history.csv` | 按 experiment ID 对比 train/validation loss 与 accuracy |
| 实验配置与摘要 | `tables/experiment_summary.csv` | 记录唯一变量、最佳验证指标、耗时和结论 |
| 基线训练曲线 | `figures/E01_learning_curves.png` | 检查收敛与过拟合 |
| 受控对比图 | `figures/controlled_experiments.png` | 比较学习率、深度和 batch size |
| 最终混淆矩阵 | `figures/final_confusion_matrix.png` | 查看类别级错误 |
| 最终错误样本 | `figures/final_misclassified_samples.png` | 分析笔画与类别混淆 |
| 最终指标 | `tables/final_test_metrics.json` | 保留一次性测试结果 |
| 模型权重 | `models/final_state_dict.pt` | 重新加载后推理 |
| 模型与预处理配置 | `models/final_model_config.json` | 重建与权重匹配的模型 |
| 加载一致性结果 | `tables/reload_check.json` | 证明固定样本加载前后输出一致 |

## 命名规则

- 过程产物以实验 ID 开头，例如 `E02_learning_curves.png`。
- 只有锁定配置后的产物使用 `final_` 前缀。
- 结果文件必须能追溯到实验 ID、随机种子、软件版本和模型配置。
- 旧实验不使用 `latest` 或无含义的 `test2`、`new`、`final_final` 命名。
