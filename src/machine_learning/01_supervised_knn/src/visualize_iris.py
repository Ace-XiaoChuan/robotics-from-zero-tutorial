"""生成 scikit-learn 鸢尾花数据集的探索性可视化图表。"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # 允许在没有图形界面的环境中保存图片

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.datasets import load_iris


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_DIR / "outputs"


def load_iris_dataframe() -> pd.DataFrame:
    """加载鸢尾花数据，并把数值类别转换为品种名称。"""
    iris = load_iris(as_frame=True)
    dataframe = iris.frame.copy()
    dataframe["species"] = dataframe["target"].map(dict(enumerate(iris.target_names)))
    return dataframe.drop(columns="target")


def plot_feature_histograms(dataframe: pd.DataFrame, feature_columns: list[str]) -> None:
    """绘制四个特征各自的分布直方图。"""
    figure, axes = plt.subplots(2, 2, figsize=(12, 8))
    for axis, feature in zip(axes.flat, feature_columns):
        sns.histplot(data=dataframe, x=feature, hue="species", multiple="layer", bins=16, ax=axis)
        axis.set_title(f"Distribution of {feature}")

    figure.suptitle("Iris Feature Histograms", fontsize=16)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "feature_histograms.png", dpi=180, bbox_inches="tight")
    plt.close(figure)


def plot_class_counts(dataframe: pd.DataFrame) -> None:
    """绘制各品种的样本数量。"""
    figure, axis = plt.subplots(figsize=(8, 5))
    order = dataframe["species"].value_counts().index
    sns.countplot(data=dataframe, x="species", order=order, hue="species", legend=False, ax=axis)
    axis.set_title("Number of Samples per Iris Species")
    axis.set_xlabel("Species")
    axis.set_ylabel("Number of flowers")
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "class_counts.png", dpi=180, bbox_inches="tight")
    plt.close(figure)


def plot_pairwise_relationships(dataframe: pd.DataFrame, feature_columns: list[str]) -> None:
    """绘制所有特征两两之间的关系。"""
    grid = sns.pairplot(
        dataframe,
        vars=feature_columns,
        hue="species",
        diag_kind="hist",
        corner=True,
        plot_kws={"alpha": 0.75, "s": 35},
    )
    grid.figure.suptitle("Pairwise Relationships of Iris Features", y=1.02, fontsize=16)
    grid.figure.savefig(OUTPUT_DIR / "pairwise_relationships.png", dpi=180, bbox_inches="tight")
    plt.close(grid.figure)


def plot_correlation_heatmap(dataframe: pd.DataFrame, feature_columns: list[str]) -> None:
    """绘制数值特征之间的皮尔逊相关性热力图。"""
    correlation = dataframe[feature_columns].corr()
    figure, axis = plt.subplots(figsize=(9, 7))
    sns.heatmap(correlation, annot=True, fmt=".2f", cmap="coolwarm", center=0, square=True, ax=axis)
    axis.set_title("Correlation Heatmap of Iris Features")
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "correlation_heatmap.png", dpi=180, bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")

    dataframe = load_iris_dataframe()
    feature_columns = [column for column in dataframe.columns if column != "species"]

    plot_feature_histograms(dataframe, feature_columns)
    plot_class_counts(dataframe)
    plot_pairwise_relationships(dataframe, feature_columns)
    plot_correlation_heatmap(dataframe, feature_columns)

    print(f"已生成图表：{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
