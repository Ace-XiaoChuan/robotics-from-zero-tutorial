# 代码学习入口

本文行数：21行，预期阅读时长：2分钟

已实现 [01_inspect_data.py](01_inspect_data.py)：读取样本清单、统计并检查图片、保存九宫格、演示单张和批次张量。已实现 [02_prepare_splits.py](02_prepare_splits.py)：按修正后的标签分层划分训练、验证和测试集，随机种子为 42。已实现 [data.py](data.py)：`TrashDataset` 读取单张图片与清单标签，`make_dataloaders` 按默认 32 张组成批次。后续添加模型训练、评估和单张图片预测代码。

代码按学习步骤组织，使用中文注释解释“为什么做这一步”。运行命令在脚本实现并验证后补充到上一级 README。

已实现 [model.py](model.py)：加载官方 ResNet18 参数，冻结旧参数并替换三分类头，直接运行检查真实训练批次的前向结果；`set_head_training_mode` 用于后续只训练分类头的模式设置。

已实现 [loss.py](loss.py)：`build_criterion()` 创建交叉熵损失，直接运行将训练集首批分数与标签比较，保存平均损失及逐样本示例。尚不更新参数。

已实现 [train_step.py](train_step.py)：`build_optimizer()` 创建 SGD，`train_one_batch()` 完成清梯度、前向、损失、反向和更新；直接运行验证单批参数变化及冻结状态。

已实现 [train.py](train.py)：复用单批训练函数，默认运行三轮训练与验证，按验证损失保存最佳模型并检查重新加载。训练函数可选返回该批正确样本数，原单批演示接口仍返回损失。

训练增强入口：`data.py` 的 `build_transform(training=True)`，包含详细中文注释。训练集默认随机水平翻转、轻微亮度/对比度调整；验证与测试保持固定预处理。`train.py --no-augmentation` 可关闭增强，便于基线对比。

已实现 `evaluate.py`：读取完整最佳模型，使用固定测试集生成整体/分类指标、全部预测、混淆矩阵及错误图片总览。不会执行训练或更新参数。

已实现 `predict.py`：传入本地照片路径，默认加载增强版最佳模型，输出三类预测分数；支持手机 EXIF 方向修正，使用检查点记录的固定预处理。
