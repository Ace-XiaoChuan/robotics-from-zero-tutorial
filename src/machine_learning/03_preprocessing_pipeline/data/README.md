# 数据目录

本文行数：20行，预期阅读时长：1分钟

训练输入为 891 条记录的 `train.csv`，来自 Kaggle [Titanic - Machine Learning from Disaster](https://www.kaggle.com/competitions/titanic/data) 训练集的公开镜像，下载自 [Data Science Dojo 数据仓库](https://github.com/datasciencedojo/datasets/blob/master/titanic.csv)。它包含目标列 `Survived`，用于训练、数据划分和最终评估。

若之后需要竞赛推理数据，可将 Kaggle 提供的 `test.csv` 放到本目录。它没有目标列，属于竞赛提交用推理数据；本案例可以先不使用。

常见字段及建议的第一版处理方式：

| 字段 | 含义 | 第一版建议 |
| --- | --- | --- |
| `Survived` | 是否生存（目标） | 只作为标签，不能放入特征。 |
| `Pclass` | 舱位等级 | 可先按类别处理。 |
| `Sex`、`Embarked` | 类别信息 | 填补缺失值后独热编码。 |
| `Age`、`SibSp`、`Parch`、`Fare` | 数值信息 | 中位数填补；逻辑回归和 KNN 再标准化。 |
| `Name`、`Ticket`、`Cabin` | 高基数或文本字段 | 第一版可先删除，并在实验记录中说明。 |
| `PassengerId` | 标识符 | 不作为模型特征。 |

运行时将含标签的镜像数据保存为 `data/train.csv`，由切分脚本生成训练与保留测试数据。
