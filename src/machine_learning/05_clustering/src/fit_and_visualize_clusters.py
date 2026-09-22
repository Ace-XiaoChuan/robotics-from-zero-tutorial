"""拟合选定的 K-Means，并将处理后的样本用 PCA 投影到二维。"""

import argparse
import os
import tempfile
from pathlib import Path

import joblib

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "week05_clustering_mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline

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


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fit selected K-Means and save a PCA visualization.")
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH, help="输入 CSV 路径。")
    parser.add_argument("--feature-columns", help="逗号分隔的数值特征；建议显式提供。")
    parser.add_argument("--reference-label-column", help="仅在图中事后参考的类别列，绝不参与聚类。")
    parser.add_argument("--n-clusters", type=int, default=3, help="最终选择的簇数，默认 3。")
    parser.add_argument("--scaler", choices=["standard", "robust"], default="standard", help="缩放方式。")
    parser.add_argument("--clip-outliers", action="store_true", help="按 1.5 IQR 截断异常值。")
    return parser.parse_args()


def save_plot(coordinates: pd.DataFrame, reference_label_column: str | None, n_clusters: int) -> Path:
    panels = 2 if reference_label_column else 1
    figure, axes = plt.subplots(1, panels, figsize=(6 * panels, 5), squeeze=False)
    cluster_axis = axes[0, 0]
    scatter = cluster_axis.scatter(
        coordinates["pca_1"], coordinates["pca_2"], c=coordinates["cluster"], cmap="tab10", s=28, alpha=0.8
    )
    cluster_axis.set(title="PCA projection colored by K-Means cluster", xlabel="Principal component 1", ylabel="Principal component 2")
    cluster_axis.legend(*scatter.legend_elements(), title="Cluster", loc="best")
    cluster_axis.grid(alpha=0.2)
    if reference_label_column:
        reference_axis = axes[0, 1]
        for label, group in coordinates.groupby(reference_label_column, dropna=False):
            reference_axis.scatter(group["pca_1"], group["pca_2"], s=28, alpha=0.8, label=str(label))
        reference_axis.set(
            title=f"PCA projection colored by reference: {reference_label_column}",
            xlabel="Principal component 1",
            ylabel="Principal component 2",
        )
        reference_axis.legend(title=reference_label_column, loc="best")
        reference_axis.grid(alpha=0.2)
    figure.tight_layout()
    output_path = OUTPUT_DIR / "figures" / f"pca_cluster_visualization_k{n_clusters}.png"
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return output_path


def main() -> None:
    arguments = parse_arguments()
    if arguments.n_clusters < 2:
        raise ValueError("--n-clusters 至少为 2。")
    ensure_output_directories()
    data = load_data(arguments.data_path)
    if arguments.n_clusters >= len(data):
        raise ValueError("--n-clusters 必须小于样本数。")
    columns = choose_feature_columns(data, parse_columns(arguments.feature_columns), arguments.reference_label_column)
    features = data[columns]
    pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor(arguments.scaler, arguments.clip_outliers)),
            ("kmeans", KMeans(n_clusters=arguments.n_clusters, n_init=20, random_state=RANDOM_STATE)),
        ]
    )
    labels = pipeline.fit_predict(features)
    transformed = pipeline.named_steps["preprocessor"].transform(features)
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    components = pca.fit_transform(transformed)

    assignments = data.copy()
    assignments.insert(0, "source_row", data.index)
    assignments["cluster"] = labels
    assignments["pca_1"] = components[:, 0]
    assignments["pca_2"] = components[:, 1]
    assignments_path = OUTPUT_DIR / "tables" / f"cluster_assignments_k{arguments.n_clusters}.csv"
    assignments.to_csv(assignments_path, index=False)
    figure_path = save_plot(assignments, arguments.reference_label_column, arguments.n_clusters)
    joblib.dump(pipeline, OUTPUT_DIR / "models" / "kmeans_pipeline.joblib")

    reference_crosstab_path = None
    if arguments.reference_label_column:
        crosstab = pd.crosstab(assignments["cluster"], assignments[arguments.reference_label_column], margins=True)
        reference_crosstab_path = OUTPUT_DIR / "tables" / f"cluster_vs_reference_k{arguments.n_clusters}.csv"
        crosstab.to_csv(reference_crosstab_path)
    cluster_sizes = assignments["cluster"].value_counts().sort_index().to_dict()
    save_json(
        OUTPUT_DIR / "tables" / f"clustering_metadata_k{arguments.n_clusters}.json",
        {
            "data_path": str(arguments.data_path),
            "samples": len(data),
            "feature_columns": columns,
            "n_clusters": arguments.n_clusters,
            "random_state": RANDOM_STATE,
            "preprocessing": {"imputation": "median", "scaler": arguments.scaler, "clip_outliers": arguments.clip_outliers},
            "cluster_sizes": {str(key): int(value) for key, value in cluster_sizes.items()},
            "pca_explained_variance_ratio": [float(value) for value in pca.explained_variance_ratio_],
            "reference_label_column_excluded": arguments.reference_label_column,
            "reference_crosstab_path": str(reference_crosstab_path) if reference_crosstab_path else None,
            "label_warning": "cluster=0/1/... 是任意编号，不表示大小、质量或真实类别。",
        },
    )
    print(f"已拟合 K={arguments.n_clusters} 的 K-Means；各簇样本数：{cluster_sizes}")
    print(f"已保存模型、{assignments_path.name}、{figure_path.name} 与最终配置元数据。")
    if reference_crosstab_path:
        print(f"真实类别仅作事后对照：outputs/tables/{reference_crosstab_path.name}")


if __name__ == "__main__":
    main()
