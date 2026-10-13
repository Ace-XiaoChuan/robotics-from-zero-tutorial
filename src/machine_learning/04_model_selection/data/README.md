# 数据说明

本文行数：24行，预期阅读时长：1分钟

## 默认数据集：scikit-learn Digits

- 加载方式：`sklearn.datasets.load_digits()`。
- 任务：识别 `0` 到 `9` 共 10 个类别的手写数字。
- 输入：每个样本是一张 `8 × 8` 灰度图；用于传统分类器时展平成 64 个像素特征。
- 数据来源：scikit-learn 内置副本，无需单独下载。

## 数据划分约定

首次运行 `src/split_digits.py` 时，使用固定随机种子和 `stratify=y` 创建训练集与测试集。模型比较、超参数调整和学习曲线只读取训练集；测试集只允许由 `src/evaluate_final_model.py` 在最后使用一次。

默认会生成以下可复现文件：

- `train_split.csv`：1,437 条训练样本；
- `test_split.csv`：360 条保留测试样本；
- `split_metadata.json`：随机种子、类别分布和字段说明。

两个 CSV 都包含 `sample_index`（原始样本索引）、`digit`（目标标签）及 64 列 `pixel_<行>_<列>` 特征。`sample_index` 只用于追踪错误样本，绝不作为模型输入。

如将数据导出为本地文件或换用 MNIST，请在此补充：数据来源链接、下载日期、数据版本、样本数、许可证及训练/测试划分方式。
