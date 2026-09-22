"""将 K=2、K=3 的聚类结果与 Channel 做事后对照。"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "week05_clustering_mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans

from compare_k2_k3 import N_INIT, RANDOM_STATE, SCALED_COLUMNS, load_aligned_data, rank_cluster_labels


PROJECT_DIR = Path(__file__).resolve().parents[1]
TABLE_PATH = PROJECT_DIR / "outputs" / "tables" / "k2_k3_channel_comparison.csv"
FIGURE_PATH = PROJECT_DIR / "outputs" / "figures" / "k2_k3_channel_comparison.png"
CHANNEL_NAMES = {1: "Horeca", 2: "Retail"}


def build_comparison(raw: pd.DataFrame, scaled: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, int | float | str]] = []
    features = scaled[SCALED_COLUMNS]
    for k in (2, 3):
        model = KMeans(n_clusters=k, init="k-means++", n_init=N_INIT, random_state=RANDOM_STATE)
        original_labels = model.fit_predict(features)
        labels, _ = rank_cluster_labels(raw, original_labels)
        for cluster in range(k):
            cluster_channels = raw.loc[labels == cluster, "Channel"]
            cluster_size = len(cluster_channels)
            for channel_code, channel_name in CHANNEL_NAMES.items():
                count = int((cluster_channels == channel_code).sum())
                rows.append(
                    {
                        "n_clusters": k,
                        "cluster": f"C{cluster}",
                        "channel_code": channel_code,
                        "channel_name": channel_name,
                        "count": count,
                        "percentage_within_cluster": count / cluster_size * 100,
                        "cluster_size": cluster_size,
                    }
                )
    return pd.DataFrame(rows)


def plot_comparison(comparison: pd.DataFrame) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    channel_colors = {"Horeca": "#4C78A8", "Retail": "#F58518"}
    for axis, k in zip(axes, (2, 3)):
        subset = comparison.loc[comparison["n_clusters"] == k]
        percentages = subset.pivot(index="cluster", columns="channel_name", values="percentage_within_cluster")
        counts = subset.pivot(index="cluster", columns="channel_name", values="count")
        percentages = percentages[["Horeca", "Retail"]]
        counts = counts[["Horeca", "Retail"]]
        percentages.plot(
            kind="bar",
            stacked=True,
            color=[channel_colors[column] for column in percentages.columns],
            width=0.7,
            ax=axis,
        )
        for cluster_index, cluster in enumerate(percentages.index):
            bottom = 0.0
            for channel_name in percentages.columns:
                percentage = float(percentages.loc[cluster, channel_name])
                count = int(counts.loc[cluster, channel_name])
                if percentage >= 7:
                    axis.text(
                        cluster_index,
                        bottom + percentage / 2,
                        f"{count}\n{percentage:.1f}%",
                        ha="center",
                        va="center",
                        fontsize=9,
                        color="white",
                        fontweight="bold",
                    )
                bottom += percentage
        axis.set(
            title=f"K={k}",
            xlabel="Cluster (ordered by median total spending)",
            ylabel="Percentage within cluster",
            ylim=(0, 100),
        )
        axis.tick_params(axis="x", rotation=0)
        axis.grid(axis="y", alpha=0.2)
        axis.legend(title="Channel", loc="lower right")
    figure.suptitle("Post-hoc Channel Composition of K-Means Clusters")
    figure.tight_layout()
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURE_PATH, dpi=180, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    raw, scaled = load_aligned_data()
    unexpected_channels = sorted(set(raw["Channel"]) - set(CHANNEL_NAMES))
    if unexpected_channels:
        raise ValueError(f"发现未知 Channel 编码：{unexpected_channels}")

    comparison = build_comparison(raw, scaled)
    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(TABLE_PATH, index=False, float_format="%.2f")
    plot_comparison(comparison)

    print("K=2、K=3 与 Channel 的事后对照完成")
    print("Channel 未参与 log1p、RobustScaler、相关性检查或 K-Means。")
    print("Channel=1: Horeca；Channel=2: Retail。\n")
    display = comparison.pivot_table(
        index=["n_clusters", "cluster"],
        columns="channel_name",
        values=["count", "percentage_within_cluster"],
    )
    print(display.to_string(float_format=lambda value: f"{value:.1f}"))
    print(f"\n对照表：{TABLE_PATH}")
    print(f"比例图：{FIGURE_PATH}")
    print("这些结果描述关联，不是分类准确率，也不把 Channel 当作聚类标准答案。")


if __name__ == "__main__":
    main()
