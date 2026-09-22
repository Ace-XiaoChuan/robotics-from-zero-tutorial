# 数据目录

本文行数：22行，预期阅读时长：1分钟

> 迁入说明：本目录仅保留数据来源说明；下文“已下载”等描述属于原项目历史状态，数据集与划分文件未随教程迁入。

本目录已下载 891 条记录的 `train.csv`，它是 Kaggle [Titanic - Machine Learning from Disaster](https://www.kaggle.com/competitions/titanic/data) 训练集的公开镜像，下载自 [Data Science Dojo 数据仓库](https://github.com/datasciencedojo/datasets/blob/master/titanic.csv)。它包含目标列 `Survived`，可用于本周的训练、数据划分和最终评估。

若之后需要竞赛推理数据，可将 Kaggle 提供的 `test.csv` 放到本目录。它没有目标列，属于竞赛提交用推理数据；本周可以先不使用。

常见字段及建议的第一版处理方式：

| 字段 | 含义 | 第一版建议 |
| --- | --- | --- |
| `Survived` | 是否生存（目标） | 只作为标签，不能放入特征。 |
| `Pclass` | 舱位等级 | 可先按类别处理。 |
| `Sex`、`Embarked` | 类别信息 | 填补缺失值后独热编码。 |
| `Age`、`SibSp`、`Parch`、`Fare` | 数值信息 | 中位数填补；逻辑回归和 KNN 再标准化。 |
| `Name`、`Ticket`、`Cabin` | 高基数或文本字段 | 第一版可先删除，并在实验记录中说明。 |
| `PassengerId` | 标识符 | 不作为模型特征。 |

下载日期、数据版本与任何字段取舍都应记录在 `../experiment_log.md`。原始数据文件不建议提交到 Git。
