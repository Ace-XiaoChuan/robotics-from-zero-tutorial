# MNIST 代码说明

本文行数：63行，预期阅读时长：2分钟

代码分为数据探索、固定划分、DataLoader、网络结构、训练循环和训练入口。

## 已实现

| 文件 | 用途 | 输出 |
| --- | --- | --- |
| `explore_mnist.py` | 读取本地 MNIST，检查单样本与 batch，统计类别并绘制代表样本 | `outputs/figures/` 两张图，`outputs/tables/` 两份记录 |
| `data.py` | 复用划分、转换像素、建立训练/验证 DataLoader，检查首批输入 | `outputs/tables/dataloader_inspection.json` |
| `split_mnist.py` | 检查训练数据，按种子 42 划分 50,000 张训练、10,000 张验证，不读取测试集 | `outputs/tables/mnist_split_indices.json` 和 `split_summary.json` |

模型与训练代码均有中文学习注释，建议先读 `model.py`，再读 `engine.py`，最后读 `train.py`。

| 文件 | 用途 | 输出 |
| --- | --- | --- |
| `model.py` | 定义 Flatten → Linear → ReLU → Linear | `[B, 10]` 原始类别分数 |
| `engine.py` | 训练一轮更新参数；验证一轮固定参数 | 按样本汇总的 loss、accuracy、样本数 |
| `train.py` | 运行 E00 流程检查或 E01 基线，记录每轮结果 | `outputs/runs/实验ID_时间戳/` 中的配置、指标、曲线和权重 |

数据准备运行方式：

```bash
cd src/machine_learning/06_pytorch_networks
python3 src/explore_mnist.py
python3 src/split_mnist.py
python3 src/data.py
```

这些脚本使用已下载的本地数据，不训练模型。探索脚本 `explore_mnist.py` 支持 `--help` 查看参数；`data.py` 默认每批 64 张，训练时可通过 `make_dataloaders(batch_size=64, seed=42)` 获取训练与验证加载器。

训练运行方式：

```bash
python3 src/train.py --smoke
python3 src/train.py
```

上述命令在本章目录内运行，使用已安装依赖的环境，每次训练保存到独立目录。

## 共享数据契约

- 模型输入：浮点张量，batch 首维，原始 shape 为 `[B, 1, 28, 28]`。
- 模型输出：`[B, 10]` logits，不在模型末尾进行 softmax。
- 标签：`[B]` 的整数类别索引。
- 训练/验证返回值：至少包含按样本正确聚合的 loss、accuracy 和样本数。
- 运行记录：`history.csv` 每个 epoch 一行，分别记录 train/validation loss 和 accuracy、耗时；experiment ID 和配置保存在同目录的 `config.json`。

## 顺序约束

训练 batch 的核心顺序必须在实施时能清晰对应到：

1. 将输入与标签放到目标设备。
2. 清零上一次迭代留下的梯度。
3. 前向传播得到 logits。
4. 由 logits 和真实标签计算损失。
5. 反向传播计算各参数梯度。
6. 优化器根据梯度更新参数。
7. 聚合本 batch 的损失、正确数和样本数。

评估时不调用反向传播和优化器更新，并关闭梯度记录。
