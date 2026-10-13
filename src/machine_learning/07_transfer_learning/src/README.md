# 迁移学习代码入口

本文行数：21行，预期阅读时长：1分钟

代码把数据准备、模型、训练和推理分开，中文注释解释关键步骤。

| 文件 | 用途 |
| --- | --- |
| [01_inspect_data.py](01_inspect_data.py) | 检查图片、标签、类别数量与张量形状 |
| [02_prepare_splits.py](02_prepare_splits.py) | 按修正标签分层划分训练、验证与测试 |
| [data.py](data.py) | Dataset、DataLoader、固定预处理与训练增强 |
| [model.py](model.py) | 加载 ResNet18，固定骨干并替换三分类头 |
| [loss.py](loss.py) | 原始 logits 与整数标签的交叉熵 |
| [train_step.py](train_step.py) | 单批梯度清零、前向、反向与 SGD 更新 |
| [train.py](train.py) | 按轮训练、验证和保存最佳模型 |
| [evaluate.py](evaluate.py) | 测试指标、混淆矩阵、预测与错误图片 |
| [predict.py](predict.py) | 加载 checkpoint，预测本地照片 |

建议按 data → model → train_step → train 阅读。训练增强由 `build_transform(training=True)` 提供；`train.py --no-augmentation` 关闭增强，用于基线比较。

[实现与运行说明](../reference.md) · [实验结果](../results.md) · [本章入口](../README.md)
