# 聚类数据说明

本文行数：29行，预期阅读时长：2分钟

在 `src/machine_learning/05_clustering/` 下运行 `python3 src/generate_demo_data.py`，默认在本数据目录生成演示数据：

- 文件：`customer_data.csv`
- 样本数：360（每次固定随机种子生成相同结果）
- 可用聚类特征：`age`、`monthly_spending`、`visits_per_month`、`avg_session_minutes`
- 标识列：`customer_id`，仅用于追踪，不能作为输入特征
- `reference_segment`：仅为演示而保留的隐藏生成分组；只能在聚类完成后对照，不能参与训练

该数据是合成练习数据，不应用于真实业务结论。它包含三处缺失值和一处极端值，用于学习检查数据质量与异常值处理的取舍。

替换为真实数据时，请在此记录：数据来源、提取日期或版本、样本单位（每行代表什么）、字段定义、已知缺失值、许可证/隐私约束，以及哪些字段被排除和原因。敏感原始数据不建议提交到 Git。

## Wholesale Customers

- 文件：`wholesale_customers.csv`
- 来源：[UCI Machine Learning Repository：Wholesale customers](https://archive.ics.uci.edu/dataset/292/wholesale%2Bcustomers)
- 许可证：[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- 样本数：440；每行代表一位批发分销商客户。
- 完整性校验（SHA-256）：`c3d018c643565b85cee733c4a2ac76dd76e080e857cb23f0ccfcc2e15a6c17ef`

建议用于聚类的六个连续数值特征均为年消费额（货币单位未公开）：`Fresh`、`Milk`、`Grocery`、`Frozen`、`Detergents_Paper`、`Delicassen`。数据没有缺失值，但消费额分布偏斜且可能有大客户，适合练习缩放、异常值诊断和簇画像。

字段含义：`Fresh` 为生鲜产品，`Milk` 为牛奶/乳制品，`Grocery` 为杂货，`Frozen` 为冷冻食品，`Detergents_Paper` 为清洁剂和纸制品，`Delicassen` 为熟食产品的年消费额。字段名 `Delicassen` 沿用原始数据拼写。

`Channel` 与 `Region` 是已有的类别/分组信息，不要作为 K-Means 的输入特征。可在聚类完成后用其中一个作为参考，检查聚类和已知分组是否存在关系；这种对照不能说明聚类“预测正确”。
