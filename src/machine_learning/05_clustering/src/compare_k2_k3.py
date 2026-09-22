"""公平比较 K=2 与 K=3 的 PCA 投影和原始金额簇画像。"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "week05_clustering_mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA


PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = PROJECT_DIR / "data" / "wholesale_customers.csv"
SCALED_DATA_PATH = PROJECT_DIR / "outputs" / "tables" / "wholesale_customers_log1p_robust_scaled.csv"
PROFILE_TABLE_PATH = PROJECT_DIR / "outputs" / "tables" / "k2_k3_cluster_profiles.csv"
PCA_FIGURE_PATH = PROJECT_DIR / "outputs" / "figures" / "k2_k3_pca_comparison.png"
PROFILE_FIGURE_PATH = PROJECT_DIR / "outputs" / "figures" / "k2_k3_profile_heatmap.png"
RANDOM_STATE = 42
N_INIT = 20
FEATURES = ["Fresh", "Milk", "Grocery", "Frozen", "Detergents_Paper", "Delicassen"]
SCALED_COLUMNS = [f"{feature}_log1p_robust_scaled" for feature in FEATURES]


def load_aligned_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_csv(RAW_DATA_PATH)
    scaled = pd.read_csv(SCALED_DATA_PATH)
    if len(raw) != len(scaled):
        raise ValueError("原始数据与缩放数据的客户数不一致。")
    required_scaled = ["customer_row", "Channel", "Region", *SCALED_COLUMNS]
    missing = [column for column in required_scaled if column not in scaled.columns]
    if missing:
        raise ValueError(f"缩放数据缺少字段：{missing}")
    expected_rows = np.arange(1, len(raw) + 1)
    if not np.array_equal(scaled["customer_row"].to_numpy(), expected_rows):
        raise ValueError("customer_row 与原始 CSV 行顺序不一致。")
    if not np.array_equal(raw["Channel"].to_numpy(), scaled["Channel"].to_numpy()):
        raise ValueError("Channel 在原始数据与缩放数据之间不一致。")
    if not np.array_equal(raw["Region"].to_numpy(), scaled["Region"].to_numpy()):
        raise ValueError("Region 在原始数据与缩放数据之间不一致。")
    if not np.isfinite(scaled[SCALED_COLUMNS].to_numpy()).all():
        raise ValueError("缩放特征中存在缺失值或无穷值。")
    return raw, scaled


def rank_cluster_labels(raw: pd.DataFrame, labels: np.ndarray) -> tuple[np.ndarray, dict[int, int]]:
    """按每位客户六类总消费额的簇内中位数排序，使 C0→C1→C2 便于比较。"""
    total_spending = raw[FEATURES].sum(axis=1)
    median_total_by_label = total_spending.groupby(labels).median().sort_values()
    label_map = {int(original_label): rank for rank, original_label in enumerate(median_total_by_label.index)}
    ranked_labels = np.array([label_map[int(label)] for label in labels], dtype=int)
    return ranked_labels, label_map


def build_profiles(raw: pd.DataFrame, labels: np.ndarray, k: int) -> list[dict[str, int | float | str]]:
    rows: list[dict[str, int | float | str]] = []
    total_spending = raw[FEATURES].sum(axis=1)
    for cluster in range(k):
        mask = labels == cluster
        cluster_data = raw.loc[mask, FEATURES]
        row: dict[str, int | float | str] = {
            "n_clusters": k,
            "cluster": f"C{cluster}",
            "cluster_order_note": "ordered by median total annual spending, low to high",
            "sample_count": int(mask.sum()),
            "sample_share": float(mask.mean()),
            "median_total_annual_spending": float(total_spending.loc[mask].median()),
        }
        for feature in FEATURES:
            row[f"{feature}_median"] = float(cluster_data[feature].median())
            row[f"{feature}_mean"] = float(cluster_data[feature].mean())
        rows.append(row)
    return rows


def plot_pca_comparison(
    coordinates: np.ndarray,
    pca: PCA,
    models: dict[int, KMeans],
    labels_by_k: dict[int, np.ndarray],
    label_maps: dict[int, dict[int, int]],
) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharex=True, sharey=True)
    colors = plt.get_cmap("tab10")
    for axis, k in zip(axes, (2, 3)):
        labels = labels_by_k[k]
        for cluster in range(k):
            mask = labels == cluster
            axis.scatter(
                coordinates[mask, 0],
                coordinates[mask, 1],
                s=28,
                alpha=0.72,
                color=colors(cluster),
                label=f"C{cluster} (n={int(mask.sum())})",
            )
        center_frame = pd.DataFrame(models[k].cluster_centers_, columns=SCALED_COLUMNS)
        projected_centers = pca.transform(center_frame)
        for original_label, ranked_label in label_maps[k].items():
            center = projected_centers[original_label]
            axis.scatter(center[0], center[1], marker="X", s=180, color=colors(ranked_label), edgecolor="black")
        axis.set(title=f"K={k}", xlabel="Principal component 1", ylabel="Principal component 2")
        axis.grid(alpha=0.2)
        axis.legend(title="Cluster", loc="best")
    explained = pca.explained_variance_ratio_.sum() * 100
    figure.suptitle(f"Same PCA projection, different K-Means labels (PC1+PC2 explain {explained:.1f}% variance)")
    figure.tight_layout()
    PCA_FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(PCA_FIGURE_PATH, dpi=180, bbox_inches="tight")
    plt.close(figure)


def plot_profile_heatmap(profiles: pd.DataFrame, raw: pd.DataFrame) -> None:
    overall_medians = raw[FEATURES].median()
    ratios = profiles[[f"{feature}_median" for feature in FEATURES]].copy()
    ratios.columns = FEATURES
    ratios = ratios.div(overall_medians, axis="columns")
    log2_ratios = np.log2(ratios)
    row_labels = [
        f"K={int(row.n_clusters)} {row.cluster} (n={int(row.sample_count)})" for row in profiles.itertuples(index=False)
    ]
    ratio_annotations = ratios.map(lambda value: f"{value:.2f}×")

    figure, axis = plt.subplots(figsize=(11, 5.5))
    sns.heatmap(
        log2_ratios,
        annot=ratio_annotations,
        fmt="",
        cmap="coolwarm",
        center=0,
        linewidths=0.5,
        xticklabels=FEATURES,
        yticklabels=row_labels,
        cbar_kws={"label": "log2(cluster median / overall median)"},
        ax=axis,
    )
    axis.set(
        title="Cluster profiles in original spending units (annotations are ratios to overall median)",
        xlabel="Original spending feature",
        ylabel="Candidate solution and cluster",
    )
    axis.tick_params(axis="x", rotation=35)
    figure.tight_layout()
    PROFILE_FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(PROFILE_FIGURE_PATH, dpi=180, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    raw, scaled = load_aligned_data()
    features = scaled[SCALED_COLUMNS]
    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    coordinates = pca.fit_transform(features)

    models: dict[int, KMeans] = {}
    labels_by_k: dict[int, np.ndarray] = {}
    label_maps: dict[int, dict[int, int]] = {}
    profile_rows: list[dict[str, int | float | str]] = []
    original_labels_by_k: dict[int, np.ndarray] = {}
    for k in (2, 3):
        model = KMeans(n_clusters=k, init="k-means++", n_init=N_INIT, random_state=RANDOM_STATE)
        original_labels = model.fit_predict(features)
        ranked_labels, label_map = rank_cluster_labels(raw, original_labels)
        models[k] = model
        original_labels_by_k[k] = original_labels
        labels_by_k[k] = ranked_labels
        label_maps[k] = label_map
        profile_rows.extend(build_profiles(raw, ranked_labels, k))

    profiles = pd.DataFrame(profile_rows)
    PROFILE_TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    profiles.to_csv(PROFILE_TABLE_PATH, index=False, float_format="%.3f")
    plot_pca_comparison(coordinates, pca, models, labels_by_k, label_maps)
    plot_profile_heatmap(profiles, raw)

    cross_tab = pd.crosstab(labels_by_k[2], labels_by_k[3], rownames=["K=2"], colnames=["K=3"])
    print("K=2 与 K=3 比较完成")
    print(f"客户数：{len(raw)}；输入：六个 log1p + RobustScaler 特征；截断：否")
    print(f"PCA 前两主成分解释方差：{pca.explained_variance_ratio_[0]:.3f} + {pca.explained_variance_ratio_[1]:.3f} = {pca.explained_variance_ratio_.sum():.3f}")
    print("\nK=2 的簇如何被 K=3 重新划分（只输出到终端，不另存 CSV）：")
    print(cross_tab.to_string())
    print("\n簇画像概要：")
    print(profiles[["n_clusters", "cluster", "sample_count", "sample_share", "median_total_annual_spending"]].to_string(index=False))
    print(f"\nPCA 对比图：{PCA_FIGURE_PATH}")
    print(f"画像热力图：{PROFILE_FIGURE_PATH}")
    print(f"合并画像表：{PROFILE_TABLE_PATH}")
    print("尚未选择最终 K，也未使用 Channel 参与聚类或画像排序。")


if __name__ == "__main__":
    main()
