# 实验产物

本文行数：24行，预期阅读时长：2分钟

当前数据探索与加载产物：

- `figures/sample_grid.png`：固定种子 42，每类抽三张的九宫格。
- `tables/inspection_summary.json`：类别数量、实际图片格式、抽样路径及张量演示结果。

重新运行 `src/01_inspect_data.py` 会更新这两个文件。

`tables/dataloader_summary.json` 由 `src/data.py` 生成，记录预处理、批次形状、数量及像素范围。尚无模型训练和评估结果，后续保存训练曲线、评估指标、混淆矩阵、错误样本和模型权重。

错误样本应能看出原图、真实类别和预测类别，方便回顾模型容易混淆什么。每次实验的主要发现写入上一级 experiment_log.md。

模型准备产物：`pretrained/resnet18-f37072fd.pth` 为官方原始权重缓存（忽略 Git），`tables/model_summary.json` 为单批前向检查记录。尚未保存本周训练后的模型。

`tables/loss_summary.json` 由 `src/loss.py` 生成，记录首个训练批次的交叉熵损失，包含前三张样本的标签、分数和单张损失，不是训练或评估成绩。

`tables/train_step_summary.json` 记录一次真实训练批次的参数更新，包括更新前后同批损失、梯度范数与参数变化。未保存这一步更新后的模型权重，仍未完成整轮训练和最终评估。

完整轮次实验保存在 `runs/<时间戳>/`：`history.json` 为逐轮指标，`best_model.pt` 为验证损失最低的模型与配置（权重忽略 Git）。每次运行使用新目录，先前单批检查记录保留。

2026-09-21：增强版三轮训练与两版本测试评估已完成。详细结果与产物索引见项目 README 的“测试评估与增强版训练”小节。
