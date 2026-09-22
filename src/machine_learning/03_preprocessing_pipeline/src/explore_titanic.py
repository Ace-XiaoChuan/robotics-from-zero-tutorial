"""绘制泰坦尼克号第一版七个特征的分布图。"""

import argparse
import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "week03_titanic_mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_DIR / "data" / "train.csv"
OUTPUT_PATH = PROJECT_DIR / "outputs" / "figures" / "feature_distributions.png"
FEATURE_COLUMNS = ["Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"]
CATEGORICAL_OR_DISCRETE_COLUMNS = ["Pclass", "Sex", "SibSp", "Parch", "Embarked"]
CONTINUOUS_COLUMNS = ["Age", "Fare"]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot distributions for Titanic's seven selected features.")
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH, help="原始训练数据 CSV 路径。")
    parser.add_argument("--output-path", type=Path, default=OUTPUT_PATH, help="PNG 输出路径。")
    return parser.parse_args()


def plot_bar_proportions(axis: plt.Axes, values: pd.Series, column: str) -> None:
    """为类别或离散特征绘制各取值的样本占比。"""
    labeled_values = values.fillna("Missing").astype(str)
    proportions = labeled_values.value_counts(normalize=True, sort=False).mul(100)
    if column in {"Pclass", "SibSp", "Parch"}:
        proportions = proportions.sort_index(key=lambda index: pd.to_numeric(index, errors="coerce"))

    bars = axis.bar(proportions.index, proportions.values, color="#4C78A8")
    axis.set_title(column)
    axis.set_ylabel("Sample proportion (%)")
    axis.set_ylim(0, max(proportions.max() * 1.18, 10))
    axis.tick_params(axis="x", rotation=35 if column == "Embarked" else 0)
    for bar, proportion in zip(bars, proportions.values):
        axis.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{proportion:.1f}%", ha="center", va="bottom", fontsize=8)


def plot_continuous_proportions(axis: plt.Axes, values: pd.Series, column: str) -> None:
    """为连续特征绘制按全部样本比例计的直方图。"""
    non_missing = values.dropna()
    weights = np.full(len(non_missing), 100 / len(values))
    axis.hist(non_missing, bins=20, weights=weights, color="#72B7B2", edgecolor="white")
    missing_count = int(values.isna().sum())
    missing_ratio = missing_count / len(values) * 100
    axis.set_title(column)
    axis.set_xlabel(column)
    axis.set_ylabel("Sample proportion per bin (%)")
    axis.text(
        0.98,
        0.95,
        f"Missing: {missing_count} ({missing_ratio:.1f}%)",
        transform=axis.transAxes,
        ha="right",
        va="top",
        fontsize=9,
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.85},
    )


def main() -> None:
    arguments = parse_arguments()
    if not arguments.data_path.is_file():
        raise FileNotFoundError(f"未找到数据文件：{arguments.data_path}")

    data = pd.read_csv(arguments.data_path)
    missing_columns = [column for column in FEATURE_COLUMNS if column not in data.columns]
    if missing_columns:
        raise ValueError(f"数据缺少必需字段：{missing_columns}")

    figure, axes = plt.subplots(2, 4, figsize=(16, 8))
    flattened_axes = axes.ravel()
    for axis, column in zip(flattened_axes, CATEGORICAL_OR_DISCRETE_COLUMNS):
        plot_bar_proportions(axis, data[column], column)
    for axis, column in zip(flattened_axes[len(CATEGORICAL_OR_DISCRETE_COLUMNS) :], CONTINUOUS_COLUMNS):
        plot_continuous_proportions(axis, data[column], column)
    flattened_axes[-1].axis("off")

    figure.suptitle("Titanic: Distributions of the Seven Selected Features", fontsize=15)
    figure.tight_layout(rect=(0, 0, 1, 0.95))
    arguments.output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(arguments.output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)

    print(f"已保存七个特征的分布图：{arguments.output_path}")
    print("缺失值数量：")
    print(data[FEATURE_COLUMNS].isna().sum().to_string())


if __name__ == "__main__":
    main()
