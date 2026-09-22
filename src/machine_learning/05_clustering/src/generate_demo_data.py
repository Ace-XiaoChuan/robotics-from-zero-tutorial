"""生成可复现实验用的无标签客户数据；仅为练习，不代表真实客户。"""

from pathlib import Path

import numpy as np
import pandas as pd

from clustering_utils import DEFAULT_DATA_PATH, RANDOM_STATE


def main() -> None:
    rng = np.random.default_rng(RANDOM_STATE)
    centers = np.array([[32, 42, 3.0, 3.5], [68, 190, 9.0, 16.0], [49, 105, 5.5, 8.0]])
    spreads = np.array([[7, 18, 1.0, 1.2], [9, 35, 2.0, 4.0], [8, 25, 1.4, 2.0]])
    sizes = [120, 110, 130]
    blocks, labels = [], []
    for index, (center, spread, size) in enumerate(zip(centers, spreads, sizes)):
        blocks.append(rng.normal(center, spread, size=(size, len(center))))
        labels.extend([index] * size)
    values = np.vstack(blocks)
    data = pd.DataFrame(
        values,
        columns=["age", "monthly_spending", "visits_per_month", "avg_session_minutes"],
    )
    data["age"] = data["age"].clip(18, 85).round().astype(int)
    data["monthly_spending"] = data["monthly_spending"].clip(5).round(2)
    data["visits_per_month"] = data["visits_per_month"].clip(0.1).round(2)
    data["avg_session_minutes"] = data["avg_session_minutes"].clip(1).round(2)
    data.insert(0, "customer_id", [f"C{number:04d}" for number in range(1, len(data) + 1)])
    # 真实任务里没有这列；在本练习中它只用于事后理解，不能作为聚类输入。
    data["reference_segment"] = np.array(labels)
    for column, row in [("monthly_spending", 7), ("visits_per_month", 83), ("avg_session_minutes", 215)]:
        data.loc[row, column] = np.nan
    data.loc[12, "monthly_spending"] = 900.0  # 供异常值诊断与可选截断练习使用。

    DEFAULT_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(DEFAULT_DATA_PATH, index=False)
    print(f"已生成 {len(data)} 条演示客户数据：{DEFAULT_DATA_PATH}")
    print("聚类特征：age, monthly_spending, visits_per_month, avg_session_minutes")
    print("reference_segment 仅供事后参考，切勿作为特征传入。")


if __name__ == "__main__":
    main()
