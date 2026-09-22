"""比较多个 K-Means 簇数的惯性与轮廓系数。"""

import argparse
import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "week05_clustering_mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from clustering_utils import (
    DEFAULT_DATA_PATH,
    OUTPUT_DIR,
    RANDOM_STATE,
    build_preprocessor,
    choose_feature_columns,
    ensure_output_directories,
    load_data,
    parse_columns,
    save_json,
)


def parse_k_values(value: str) -> list[int]:
    try:
        values = sorted({int(item.strip()) for item in value.split(",")})
    except ValueError as error:
        raise ValueError("--k-values 必须是逗号分隔的整数，例如 2,3,4,5,6。") from error
    if not values or min(values) < 2:
        raise ValueError("--k-values 中的 K 必须都不小于 2。")
    return values


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare candidate cluster counts using K-Means.")
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH, help="输入 CSV 路径。")
    parser.add_argument("--feature-columns", help="逗号分隔的数值特征；建议显式提供。")
    parser.add_argument("--reference-label-column", help="仅事后参考的类别列，绝不参与聚类。")
    parser.add_argument("--k-values", default="2,3,4,5,6", help="候选 K，例如 2,3,4,5,6。")
    parser.add_argument("--scaler", choices=["standard", "robust"], default="standard", help="缩放方式。")
    parser.add_argument("--clip-outliers", action="store_true", help="按 1.5 IQR 截断异常值；先在探索阶段确认其合理性。")
    return parser.parse_args()


def save_metric_plot(results: pd.DataFrame) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(results["n_clusters"], results["inertia"], marker="o", color="#4C78A8")
    axes[0].set(title="Elbow diagnostic", xlabel="Number of clusters (K)", ylabel="Inertia (lower is expected)")
    axes[1].plot(results["n_clusters"], results["silhouette_score"], marker="o", color="#54A24B")
    axes[1].set(title="Silhouette diagnostic", xlabel="Number of clusters (K)", ylabel="Silhouette score (higher is better)")
    for axis in axes:
        axis.set_xticks(results["n_clusters"])
        axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "figures" / "cluster_count_diagnostics.png", dpi=180, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    arguments = parse_arguments()
    ensure_output_directories()
    data = load_data(arguments.data_path)
    columns = choose_feature_columns(data, parse_columns(arguments.feature_columns), arguments.reference_label_column)
    candidate_k = parse_k_values(arguments.k_values)
    if max(candidate_k) >= len(data):
        raise ValueError("每个 K 必须小于样本数，才能计算轮廓系数。")

    features = data[columns]
    preprocessor = build_preprocessor(arguments.scaler, arguments.clip_outliers)
    transformed = preprocessor.fit_transform(features)
    rows = []
    for k in candidate_k:
        model = KMeans(n_clusters=k, n_init=20, random_state=RANDOM_STATE)
        labels = model.fit_predict(transformed)
        rows.append(
            {
                "n_clusters": k,
                "inertia": float(model.inertia_),
                "silhouette_score": float(silhouette_score(transformed, labels)),
                "cluster_size_min": int(np.bincount(labels).min()),
                "cluster_size_max": int(np.bincount(labels).max()),
            }
        )
    results = pd.DataFrame(rows)
    results.to_csv(OUTPUT_DIR / "tables" / "cluster_count_comparison.csv", index=False)
    save_metric_plot(results)
    suggested_k = int(results.loc[results["silhouette_score"].idxmax(), "n_clusters"])
    save_json(
        OUTPUT_DIR / "tables" / "cluster_count_comparison.json",
        {
            "data_path": str(arguments.data_path),
            "samples": len(data),
            "feature_columns": columns,
            "reference_label_column_excluded": arguments.reference_label_column,
            "preprocessing": {"imputation": "median", "scaler": arguments.scaler, "clip_outliers": arguments.clip_outliers},
            "results": rows,
            "silhouette_suggested_k": suggested_k,
            "warning": "轮廓系数和肘部法是诊断，不会替代对簇画像、最小簇大小与业务可解释性的判断。",
        },
    )
    print("K 值比较完成（所有输入列均未包含真实类别参考列）。\n")
    print(results.to_string(index=False, float_format=lambda value: f"{value:.3f}"))
    print(f"\n按轮廓系数最高得到的候选 K：{suggested_k}；请结合图表和簇画像再决定。")
    print("已保存：outputs/tables/cluster_count_comparison.*、outputs/figures/cluster_count_diagnostics.png")


if __name__ == "__main__":
    main()
