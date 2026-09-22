"""按固定规则将泰坦尼克号训练数据划分为训练集和测试集。"""

import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_DIR / "data" / "train.csv"
DEFAULT_TRAIN_PATH = PROJECT_DIR / "data" / "train_split.csv"
DEFAULT_TEST_PATH = PROJECT_DIR / "data" / "test_split.csv"
DEFAULT_METADATA_PATH = PROJECT_DIR / "data" / "split_metadata.json"
TARGET_COLUMN = "Survived"
FEATURE_COLUMNS = ["Pclass", "Sex", "Age", "SibSp", "Parch", "Fare", "Embarked"]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split Titanic data into stratified train and test sets.")
    parser.add_argument("--data-path", type=Path, default=DEFAULT_DATA_PATH, help="原始训练数据 CSV 路径。")
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
        raise FileNotFoundError(f"未找到数据文件：{arguments.data_path}")

    data = pd.read_csv(arguments.data_path)
    required_columns = [TARGET_COLUMN, *FEATURE_COLUMNS]
    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(f"数据缺少必需字段：{missing_columns}")

    # 第一版只保留明确选定的七个输入特征与标签，避免标识符或文本字段意外进入模型。
    selected_data = data[required_columns].copy()
    train_data, test_data = train_test_split(
        selected_data,
        test_size=arguments.test_size,
        random_state=arguments.random_state,
        stratify=selected_data[TARGET_COLUMN],
        shuffle=True,
    )

    for output_path in (arguments.train_path, arguments.test_path, DEFAULT_METADATA_PATH):
        output_path.parent.mkdir(parents=True, exist_ok=True)
    train_data.to_csv(arguments.train_path, index=False)
    test_data.to_csv(arguments.test_path, index=False)

    metadata = {
        "source_file": str(arguments.data_path.relative_to(PROJECT_DIR)),
        "target_column": TARGET_COLUMN,
        "feature_columns": FEATURE_COLUMNS,
        "random_state": arguments.random_state,
        "test_size": arguments.test_size,
        "stratified_by": TARGET_COLUMN,
        "total_samples": len(selected_data),
        "train_samples": len(train_data),
        "test_samples": len(test_data),
        "class_counts": {
            "all": selected_data[TARGET_COLUMN].value_counts().sort_index().to_dict(),
            "train": train_data[TARGET_COLUMN].value_counts().sort_index().to_dict(),
            "test": test_data[TARGET_COLUMN].value_counts().sort_index().to_dict(),
        },
    }
    with DEFAULT_METADATA_PATH.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)

    print("泰坦尼克号数据切分完成")
    print(f"随机种子：{arguments.random_state}；测试集比例：{arguments.test_size:.0%}")
    print(f"训练集：{len(train_data)} 条 → {arguments.train_path}")
    print(f"测试集：{len(test_data)} 条 → {arguments.test_path}")
    print(f"切分元数据：{DEFAULT_METADATA_PATH}")


if __name__ == "__main__":
    main()
