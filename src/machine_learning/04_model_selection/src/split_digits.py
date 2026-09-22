"""为 scikit-learn 的 Digits 数据创建固定的分层训练集/测试集划分。"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

from digits_utils import (
    DATA_DIR,
    FEATURE_COLUMNS,
    IDENTIFIER_COLUMN,
    RANDOM_STATE,
    SPLIT_METADATA_PATH,
    TARGET_COLUMN,
    TEST_PATH,
    TRAIN_PATH,
    write_json,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="固定 Digits 数据集的分层训练集与测试集。")
    parser.add_argument("--random-state", type=int, default=RANDOM_STATE, help="随机种子，默认 42。")
    parser.add_argument("--test-size", type=float, default=0.2, help="测试集比例，默认 0.2。")
    parser.add_argument("--train-path", type=str, default=str(TRAIN_PATH), help="训练集 CSV 输出路径。")
    parser.add_argument("--test-path", type=str, default=str(TEST_PATH), help="测试集 CSV 输出路径。")
    return parser.parse_args()


def resolve_output_path(path_text: str) -> Path:
    """需要时从项目目录解析命令行传入的相对路径。"""
    path = Path(path_text)
    return path if path.is_absolute() else (DATA_DIR.parent / path)


def main() -> None:
    arguments = parse_arguments()
    if not 0 < arguments.test_size < 1:
        raise ValueError("--test-size 必须介于 0 和 1 之间。")

    train_path = resolve_output_path(arguments.train_path).resolve()
    test_path = resolve_output_path(arguments.test_path).resolve()

    digits = load_digits()
    data = pd.DataFrame(digits.data, columns=FEATURE_COLUMNS)
    data.insert(0, IDENTIFIER_COLUMN, data.index)
    data.insert(1, TARGET_COLUMN, digits.target.astype(int))

    train_data, test_data = train_test_split(
        data,
        test_size=arguments.test_size,
        random_state=arguments.random_state,
        stratify=data[TARGET_COLUMN],
        shuffle=True,
    )
    train_data = train_data.sort_values(IDENTIFIER_COLUMN)
    test_data = test_data.sort_values(IDENTIFIER_COLUMN)
    for output_path in (train_path, test_path, SPLIT_METADATA_PATH):
        output_path.parent.mkdir(parents=True, exist_ok=True)
    train_data.to_csv(train_path, index=False)
    test_data.to_csv(test_path, index=False)

    class_counts = {
        split_name: {str(label): int(count) for label, count in frame[TARGET_COLUMN].value_counts().sort_index().items()}
        for split_name, frame in {"all": data, "train": train_data, "test": test_data}.items()
    }
    metadata = {
        "dataset": "scikit-learn Digits via sklearn.datasets.load_digits()",
        "random_state": arguments.random_state,
        "test_size": arguments.test_size,
        "stratified_by": TARGET_COLUMN,
        "target_column": TARGET_COLUMN,
        "identifier_column": IDENTIFIER_COLUMN,
        "feature_columns": FEATURE_COLUMNS,
        "total_samples": int(len(data)),
        "train_samples": int(len(train_data)),
        "test_samples": int(len(test_data)),
        "class_counts": class_counts,
        "train_path": str(train_path.relative_to(DATA_DIR.parent)),
        "test_path": str(test_path.relative_to(DATA_DIR.parent)),
    }
    write_json(metadata, SPLIT_METADATA_PATH)

    print("Digits 分层切分完成")
    print(f"随机种子：{arguments.random_state}；测试集比例：{arguments.test_size:.0%}")
    print(f"训练集：{len(train_data)} 条 → {train_path}")
    print(f"测试集：{len(test_data)} 条 → {test_path}")
    print("测试集从现在起不应用于模型选择或调参。")


if __name__ == "__main__":
    main()
