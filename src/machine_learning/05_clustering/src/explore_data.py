"""检查聚类特征的缺失值、量纲和 IQR 异常值。"""

import argparse
import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "week05_clustering_mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from clustering_utils import (
    DEFAULT_DATA_PATH,
    OUTPUT_DIR,
    choose_feature_columns,
    ensure_output_directories,
    iqr_outlier_report,
    load_data,
    parse_columns,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Explore numeric features before K-Means clustering.")
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH, help="输入 CSV 路径。")
    parser.add_argument("--feature-columns", help="逗号分隔的数值特征；省略时自动排除 ID 列。")
    parser.add_argument("--reference-label-column", help="仅事后参考的真实类别列，绝不参与聚类。")
    return parser.parse_args()


def plot_distributions(features: pd.DataFrame) -> None:
    columns = features.columns.tolist()
    figure, axes = plt.subplots(1, len(columns), figsize=(4.2 * len(columns), 3.8), squeeze=False)
    for axis, column in zip(axes.ravel(), columns):
        axis.hist(features[column].dropna(), bins=24, color="#4C78A8", edgecolor="white")
        axis.set(title=column, xlabel=column, ylabel="Sample count")
        axis.grid(axis="y", alpha=0.2)
    figure.suptitle("Clustering feature distributions (before preprocessing)")
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "figures" / "feature_distributions.png", dpi=180, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    arguments = parse_arguments()
    ensure_output_directories()
    data = load_data(arguments.data_path)
    columns = choose_feature_columns(data, parse_columns(arguments.feature_columns), arguments.reference_label_column)
    features = data[columns].copy()

    summary = features.describe().T
    summary.insert(0, "missing_count", features.isna().sum())
    summary.insert(1, "missing_rate", features.isna().mean())
    summary.to_csv(OUTPUT_DIR / "tables" / "feature_summary.csv")
    outliers = iqr_outlier_report(features)
    outliers.to_csv(OUTPUT_DIR / "tables" / "iqr_outlier_report.csv", index=False)
    plot_distributions(features)

    print(f"共读取 {len(data)} 条样本；聚类特征：{', '.join(columns)}")
    print("\n缺失值与 IQR 异常值诊断：")
    print(outliers[["feature", "missing_count", "outlier_count"]].to_string(index=False))
    print("\n已保存：outputs/tables/feature_summary.csv、iqr_outlier_report.csv 与 figures/feature_distributions.png")
    print("提示：异常值不一定是错误。先检查业务含义，再决定是否在后续命令中加入 --clip-outliers。")


if __name__ == "__main__":
    main()
