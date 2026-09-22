"""输出每个簇的典型特征及距中心最近的代表样本。"""

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from clustering_utils import DEFAULT_DATA_PATH, OUTPUT_DIR, choose_feature_columns, ensure_output_directories, load_data, parse_columns


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile K-Means clusters and export representative samples.")
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH, help="输入 CSV 路径。")
    parser.add_argument("--feature-columns", help="必须与拟合模型时完全一致的特征列。")
    parser.add_argument("--reference-label-column", help="仅事后参考的类别列，绝不参与聚类。")
    parser.add_argument("--model-path", type=Path, default=OUTPUT_DIR / "models" / "kmeans_pipeline.joblib", help="已拟合模型路径。")
    parser.add_argument("--representatives-per-cluster", type=int, default=3, help="每簇导出的代表样本数。")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    if arguments.representatives_per_cluster < 1:
        raise ValueError("--representatives-per-cluster 至少为 1。")
    if not arguments.model_path.is_file():
        raise FileNotFoundError("未找到已拟合聚类模型；请先运行 src/fit_and_visualize_clusters.py。")
    ensure_output_directories()
    data = load_data(arguments.data_path)
    columns = choose_feature_columns(data, parse_columns(arguments.feature_columns), arguments.reference_label_column)
    pipeline = joblib.load(arguments.model_path)
    expected_columns = list(pipeline.feature_names_in_)
    if columns != expected_columns:
        raise ValueError(f"特征列必须与模型一致。模型使用：{expected_columns}；当前使用：{columns}")
    features = data[columns]
    labels = pipeline.predict(features)
    transformed = pipeline.named_steps["preprocessor"].transform(features)
    centers = pipeline.named_steps["kmeans"].cluster_centers_
    distances = np.linalg.norm(transformed - centers[labels], axis=1)

    assigned = data.copy()
    assigned.insert(0, "source_row", data.index)
    assigned["cluster"] = labels
    assigned["distance_to_cluster_center"] = distances
    profiles = assigned.groupby("cluster")[columns].agg(["count", "mean", "median", "min", "max"]).T
    profiles.to_csv(OUTPUT_DIR / "tables" / "cluster_feature_profiles.csv")
    size_table = assigned.groupby("cluster").size().rename("sample_count").to_frame()
    size_table["sample_share"] = size_table["sample_count"] / len(assigned)
    size_table.to_csv(OUTPUT_DIR / "tables" / "cluster_sizes.csv")
    representatives = (
        assigned.sort_values(["cluster", "distance_to_cluster_center"])
        .groupby("cluster", group_keys=False)
        .head(arguments.representatives_per_cluster)
    )
    representatives.to_csv(OUTPUT_DIR / "tables" / "cluster_representative_samples.csv", index=False)
    print("簇画像已保存：")
    print("- outputs/tables/cluster_feature_profiles.csv（每簇均值、中位数、范围）")
    print("- outputs/tables/cluster_sizes.csv")
    print("- outputs/tables/cluster_representative_samples.csv（距离中心最近，不等于‘最典型的人’的唯一标准）")
    print("\n各簇规模：")
    print(size_table.to_string())


if __name__ == "__main__":
    main()
