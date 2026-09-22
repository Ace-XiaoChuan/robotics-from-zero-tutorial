"""按固定随机种子将 Ames Housing 数据划分为训练集和测试集。"""

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_DIR / "data" / "AmesHousing.txt"
DEFAULT_TRAIN_PATH = PROJECT_DIR / "data" / "train.csv"
DEFAULT_TEST_PATH = PROJECT_DIR / "data" / "test.csv"
DEFAULT_METADATA_PATH = PROJECT_DIR / "data" / "split_metadata.json"
TARGET_COLUMN = "SalePrice"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split Ames Housing into training and test sets.")
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH, help="原始 TSV 数据路径。")
    parser.add_argument("--train-path", type=Path, default=DEFAULT_TRAIN_PATH, help="训练集 CSV 输出路径。")
    parser.add_argument("--test-path", type=Path, default=DEFAULT_TEST_PATH, help="测试集 CSV 输出路径。")
    parser.add_argument("--random-state", type=int, default=42, help="随机种子，默认 42。")
    parser.add_argument("--test-size", type=float, default=0.2, help="测试集比例，默认 0.2。")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    if not 0 < arguments.test_size < 1:
        raise ValueError("--test-size 必须介于 0 和 1 之间。")
    if not arguments.data_path.is_file():
        raise FileNotFoundError(f"未找到原始数据文件：{arguments.data_path}")

    data = pd.read_csv(arguments.data_path, sep="\t")
    if TARGET_COLUMN not in data.columns:
        raise ValueError(f"数据中没有目标列 {TARGET_COLUMN!r}。")

    # 回归目标是连续值，通常不能像分类标签那样直接按类别分层；这里使用可复现的随机切分。
    train_data, test_data = train_test_split(
        data,
        test_size=arguments.test_size,
        random_state=arguments.random_state,
        shuffle=True,
    )

    for output_path in (arguments.train_path, arguments.test_path, DEFAULT_METADATA_PATH):
        output_path.parent.mkdir(parents=True, exist_ok=True)

    train_data.to_csv(arguments.train_path, index=False)
    test_data.to_csv(arguments.test_path, index=False)

    metadata = {
        "source_file": str(arguments.data_path.relative_to(PROJECT_DIR)),
        "random_state": arguments.random_state,
        "test_size": arguments.test_size,
        "train_size": 1 - arguments.test_size,
        "total_samples": len(data),
        "train_samples": len(train_data),
        "test_samples": len(test_data),
        "target_column": TARGET_COLUMN,
    }
    with DEFAULT_METADATA_PATH.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)

    print("Ames Housing 数据切分完成")
    print(f"随机种子：{arguments.random_state}")
    print(f"训练集：{len(train_data)} 条（{len(train_data) / len(data):.1%}）→ {arguments.train_path}")
    print(f"测试集：{len(test_data)} 条（{len(test_data) / len(data):.1%}）→ {arguments.test_path}")
    print(f"切分元数据：{DEFAULT_METADATA_PATH}")


if __name__ == "__main__":
    main()
