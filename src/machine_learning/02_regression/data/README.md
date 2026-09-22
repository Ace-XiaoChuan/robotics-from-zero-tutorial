# Ames Housing 数据说明

本文行数：38行，预期阅读时长：1分钟

> 迁入说明：本目录仅保留数据来源说明；下文“已下载”等描述属于原项目历史状态，数据集与划分文件未随教程迁入。

- 文件：`AmesHousing.txt`
- 格式：UTF-8 文本，制表符分隔（TSV）
- 样本数：2,930
- 字段数：82
- 目标列：`SalePrice`（房屋成交价）
- 数据来源：[Ames Housing 数据发布页](https://jse.amstat.org/v19n3/decock/AmesHousing.txt)
- 下载日期：2026-08-19

读取示例：

```python
import pandas as pd

data = pd.read_csv("data/AmesHousing.txt", sep="\t")
```

`Order` 为数据记录顺序，`PID` 为房屋标识符。两者通常不应直接输入基线模型，以免模型利用无法泛化的编号模式。

## 固定的数据划分

已用 `random_state=42` 将完整数据随机划分为：

- `train.csv`：2,344 条记录（80%），仅用于拟合预处理规则和模型。
- `test.csv`：586 条记录（20%），在模型方案确定前不参与调参，只用于最终评估。
- `split_metadata.json`：切分比例、随机种子、样本数和目标列等可复现信息。

重新生成同一划分：

```bash
source ~/mujoco-env/bin/activate
python src/split_ames.py --random-state 42 --test-size 0.2
```
