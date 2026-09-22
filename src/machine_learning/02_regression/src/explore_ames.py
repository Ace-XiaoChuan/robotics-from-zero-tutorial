"""加载 Ames Housing 数据并完成第 2 周的基础探索。"""

import argparse
import os
import tempfile
from pathlib import Path

# 在无图形界面的终端中也能保存图片，并把 Matplotlib 缓存放到可写的临时目录。
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "week02_regression_mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_DIR / "data" / "AmesHousing.txt"
OUTPUT_DIR = PROJECT_DIR / "outputs"
TARGET_COLUMN = "SalePrice"

# 这几列兼顾数值和类别特征，便于初步观察“房屋特征 → 房价”的样子。
SAMPLE_FEATURES = [
    "Overall Qual",
    "Gr Liv Area",
    "Year Built",
    "Total Bsmt SF",
    "Neighborhood",
]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Explore the Ames Housing dataset.")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help="AmesHousing.txt 的路径。",
    )
    parser.add_argument("--rows", type=int, default=8, help="打印的样本行数，默认 8。")
    parser.add_argument("--histogram-bins", type=int, default=16, help="直方图分箱数，默认 16。")
    return parser.parse_args()


def print_section(title: str) -> None:
    print(f"\n{'=' * 12} {title} {'=' * 12}")


def print_data_overview(data: pd.DataFrame) -> None:
    numeric_columns = data.select_dtypes(include="number").columns
    categorical_columns = data.select_dtypes(exclude="number").columns

    print_section("数据概览")
    print(f"样本数：{len(data)}")
    print(f"字段数：{data.shape[1]}（数值字段 {len(numeric_columns)} 个；类别/文本字段 {len(categorical_columns)} 个）")
    print(f"目标列：{TARGET_COLUMN}（缺失值：{data[TARGET_COLUMN].isna().sum()}）")
    print("前 12 个字段：" + "、".join(data.columns[:12]))


def print_sample_rows(data: pd.DataFrame, rows: int) -> None:
    available_features = [column for column in SAMPLE_FEATURES if column in data.columns]
    columns_to_show = available_features + [TARGET_COLUMN]

    print_section(f"前 {rows} 个房屋样本：典型特征与房价")
    print(data.loc[:, columns_to_show].head(rows).to_string(index=False))


def print_missing_values(data: pd.DataFrame) -> None:
    missing_counts = data.isna().sum().sort_values(ascending=False)
    missing_counts = missing_counts[missing_counts > 0]

    print_section("缺失值最多的字段（前 10 个）")
    if missing_counts.empty:
        print("数据中没有缺失值。")
        return

    summary = pd.DataFrame(
        {
            "缺失数": missing_counts.head(10),
            "缺失比例": (missing_counts.head(10) / len(data)).map("{:.1%}".format),
        }
    )
    print(summary.to_string())


def print_sale_price_distribution(data: pd.DataFrame) -> pd.Series:
    sale_price = data[TARGET_COLUMN].dropna()
    statistics = sale_price.describe(percentiles=[0.01, 0.25, 0.5, 0.75, 0.99])

    print_section("房价 SalePrice 分布")
    print(statistics.to_string(float_format=lambda value: f"{value:,.2f}"))
    print(f"偏度：{sale_price.skew():.3f}（正值表示右侧长尾，即少量高价房拉长分布）")

    price_bins = pd.cut(sale_price, bins=10)
    bin_counts = price_bins.value_counts(sort=False)
    print("\n按房价区间统计（10 个等宽区间）：")
    for interval, count in bin_counts.items():
        print(f"{interval.left:>10,.0f} ~ {interval.right:>10,.0f}：{count:>4} 套")

    return sale_price


def save_sale_price_histogram(sale_price: pd.Series, bins: int) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "saleprice_distribution.png"

    figure, axis = plt.subplots(figsize=(9, 5))
    axis.hist(sale_price, bins=bins, color="#4C78A8", edgecolor="white", alpha=0.9)
    axis.axvline(sale_price.mean(), color="#E45756", linestyle="--", label=f"Mean: {sale_price.mean():,.0f}")
    axis.axvline(sale_price.median(), color="#54A24B", linestyle="--", label=f"Median: {sale_price.median():,.0f}")
    axis.set_title("Ames Housing: SalePrice Distribution")
    axis.set_xlabel("SalePrice (USD)")
    axis.set_ylabel("Number of houses")
    axis.ticklabel_format(style="plain", axis="x")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)
    return output_path


def main() -> None:
    arguments = parse_arguments()
    if arguments.rows < 1:
        raise ValueError("--rows 必须至少为 1。")
    if arguments.histogram_bins < 1:
        raise ValueError("--histogram-bins 必须至少为 1。")
    if not arguments.data_path.is_file():
        raise FileNotFoundError(f"未找到数据文件：{arguments.data_path}")

    # AmesHousing.txt 是制表符分隔的 TSV 文件；不在此阶段修改原始数据。
    data = pd.read_csv(arguments.data_path, sep="\t")
    if TARGET_COLUMN not in data.columns:
        raise ValueError(f"数据中没有目标列 {TARGET_COLUMN!r}。")

    print(f"已加载数据：{arguments.data_path}")
    print_data_overview(data)
    print_sample_rows(data, arguments.rows)
    print_missing_values(data)
    sale_price = print_sale_price_distribution(data)
    output_path = save_sale_price_histogram(sale_price, arguments.histogram_bins)
    print(f"\n房价直方图已保存到：{output_path}")


if __name__ == "__main__":
    main()
