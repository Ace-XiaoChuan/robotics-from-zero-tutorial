"""使用已经确认的 log1p + RobustScaler 特征比较候选 K。"""

from __future__ import annotations

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


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_DIR / "outputs" / "tables" / "wholesale_customers_log1p_robust_scaled.csv"
DEFAULT_TABLE_PATH = PROJECT_DIR / "outputs" / "tables" / "k_candidate_comparison.csv"
DEFAULT_FIGURE_PATH = PROJECT_DIR / "outputs" / "figures" / "k_candidate_diagnostics.png"
RANDOM_STATE = 42
N_INIT = 20
FEATURES = ["Fresh", "Milk", "Grocery", "Frozen", "Detergents_Paper", "Delicassen"]
SCALED_COLUMNS = [f"{feature}_log1p_robust_scaled" for feature in FEATURES]
EXCLUDED_COLUMNS = ["customer_row", "Channel", "Region"]


def parse_k_values(value: str) -> list[int]:
    try:
        values = sorted({int(item.strip()) for item in value.split(",")})
    except ValueError as error:
        raise ValueError("--k-values 必须是逗号分隔的整数，例如 2,3,4,5,6。") from error
    if not values or min(values) < 2:
        raise ValueError("候选 K 必须都是不小于 2 的整数。")
    return values


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare K=2..6 on the confirmed log1p + RobustScaler features.")
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH, help="缩放后特征 CSV 路径。")
    parser.add_argument("--k-values", default="2,3,4,5,6", help="逗号分隔的候选 K，默认 2,3,4,5,6。")
    parser.add_argument("--table-path", type=Path, default=DEFAULT_TABLE_PATH, help="指标表输出路径。")
    parser.add_argument("--figure-path", type=Path, default=DEFAULT_FIGURE_PATH, help="诊断图输出路径。")
    return parser.parse_args()


def load_confirmed_features(data_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    if not data_path.is_file():
        raise FileNotFoundError(f"未找到缩放后数据：{data_path}")
    data = pd.read_csv(data_path)
    missing_columns = [column for column in [*EXCLUDED_COLUMNS, *SCALED_COLUMNS] if column not in data.columns]
    if missing_columns:
        raise ValueError(f"缩放后数据缺少必需字段：{missing_columns}")

    features = data[SCALED_COLUMNS].copy()
    if features.isna().any().any():
        raise ValueError("六个缩放特征中仍有缺失值，不能开始 K-Means。")
    if not np.isfinite(features.to_numpy()).all():
        raise ValueError("六个缩放特征中存在无穷值，不能开始 K-Means。")
    return data, features


def compare_candidates(features: pd.DataFrame, candidate_k: list[int]) -> pd.DataFrame:
    if max(candidate_k) >= len(features):
        raise ValueError("候选 K 必须小于客户数量。")

    rows: list[dict[str, int | float | str]] = []
    previous_inertia: float | None = None
    for k in candidate_k:
        model = KMeans(
            n_clusters=k,
            init="k-means++",
            n_init=N_INIT,
            random_state=RANDOM_STATE,
        )
        labels = model.fit_predict(features)
        sizes = np.sort(np.bincount(labels))
        inertia_decrease = np.nan if previous_inertia is None else previous_inertia - model.inertia_
        inertia_decrease_pct = np.nan if previous_inertia is None else inertia_decrease / previous_inertia * 100
        rows.append(
            {
                "n_clusters": k,
                "inertia": float(model.inertia_),
                "inertia_decrease_from_previous_k": float(inertia_decrease),
                "inertia_decrease_percent": float(inertia_decrease_pct),
                "silhouette_score": float(silhouette_score(features, labels)),
                "cluster_size_min": int(sizes[0]),
                "cluster_size_max": int(sizes[-1]),
                "cluster_sizes_sorted": "|".join(str(int(size)) for size in sizes),
                "n_iter": int(model.n_iter_),
            }
        )
        previous_inertia = float(model.inertia_)
    return pd.DataFrame(rows)


def save_diagnostic_plot(results: pd.DataFrame, figure_path: Path) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    axes[0].plot(results["n_clusters"], results["inertia"], marker="o", linewidth=2, color="#4C78A8")
    axes[0].set(title="Elbow diagnostic", xlabel="Number of clusters (K)", ylabel="Inertia")
    for k, value in zip(results["n_clusters"], results["inertia"]):
        axes[0].annotate(f"{value:.1f}", (k, value), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8)

    axes[1].plot(
        results["n_clusters"], results["silhouette_score"], marker="o", linewidth=2, color="#54A24B"
    )
    axes[1].set(title="Silhouette diagnostic", xlabel="Number of clusters (K)", ylabel="Silhouette score")
    for k, value in zip(results["n_clusters"], results["silhouette_score"]):
        axes[1].annotate(f"{value:.3f}", (k, value), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8)

    for axis in axes:
        axis.set_xticks(results["n_clusters"])
        axis.grid(alpha=0.25)
    figure.suptitle("K-Means Candidate K Comparison: log1p + RobustScaler, No Clipping")
    figure.tight_layout()
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(figure_path, dpi=180, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    arguments = parse_arguments()
    candidate_k = parse_k_values(arguments.k_values)
    data, features = load_confirmed_features(arguments.data_path)
    results = compare_candidates(features, candidate_k)

    arguments.table_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(arguments.table_path, index=False, float_format="%.6f")
    save_diagnostic_plot(results, arguments.figure_path)

    print("候选 K 比较完成")
    print(f"客户数：{len(data)}；输入特征数：{features.shape[1]}")
    print(f"输入列：{', '.join(SCALED_COLUMNS)}")
    print(f"明确排除：{', '.join(EXCLUDED_COLUMNS)}")
    print(f"预处理：log1p + RobustScaler；IQR 截断：否")
    print(f"K-Means：init=k-means++，n_init={N_INIT}，random_state={RANDOM_STATE}\n")
    display_columns = [
        "n_clusters",
        "inertia",
        "inertia_decrease_percent",
        "silhouette_score",
        "cluster_size_min",
        "cluster_size_max",
        "cluster_sizes_sorted",
    ]
    print(results[display_columns].to_string(index=False, float_format=lambda value: f"{value:.3f}"))
    print(f"\n指标表：{arguments.table_path}")
    print(f"诊断图：{arguments.figure_path}")
    print("本阶段只比较候选 K；尚未选择最终 K，也未生成 PCA 图或簇画像。")


if __name__ == "__main__":
    main()
