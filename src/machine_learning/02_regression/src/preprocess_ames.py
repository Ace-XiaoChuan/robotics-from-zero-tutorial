"""在训练集上拟合 Ames Housing 预处理器，并转换训练集和测试集。"""

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TRAIN_PATH = PROJECT_DIR / "data" / "train.csv"
DEFAULT_TEST_PATH = PROJECT_DIR / "data" / "test.csv"
OUTPUT_DIR = PROJECT_DIR / "outputs" / "preprocessed"
TARGET_COLUMN = "SalePrice"
IDENTIFIER_COLUMNS = ["Order", "PID"]

# 它们虽然以数字形式存储，但数字代表代码或月份类别，而不是可直接比较的连续量。
FORCE_CATEGORICAL_COLUMNS = ["MS SubClass", "Mo Sold"]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Preprocess Ames Housing train/test data without leakage.")
    parser.add_argument("--train-path", type=Path, default=DEFAULT_TRAIN_PATH, help="训练集 CSV 路径。")
    parser.add_argument("--test-path", type=Path, default=DEFAULT_TEST_PATH, help="测试集 CSV 路径。")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help="预处理产物目录。")
    return parser.parse_args()


def load_features_and_target(data_path: Path) -> tuple[pd.DataFrame, pd.Series]:
    """读取一个已划分的数据集，分离目标列并删除无泛化意义的标识符。"""
    if not data_path.is_file():
        raise FileNotFoundError(f"未找到数据文件：{data_path}")

    data = pd.read_csv(data_path)
    if TARGET_COLUMN not in data.columns:
        raise ValueError(f"数据中没有目标列 {TARGET_COLUMN!r}：{data_path}")

    y = data[TARGET_COLUMN].copy()
    x = data.drop(columns=[TARGET_COLUMN, *IDENTIFIER_COLUMNS], errors="ignore").copy()
    return x, y


def identify_feature_columns(features: pd.DataFrame) -> tuple[list[str], list[str]]:
    """根据字段含义和 pandas 类型返回数值列、类别列。"""
    forced_categories = [column for column in FORCE_CATEGORICAL_COLUMNS if column in features.columns]
    inferred_numeric = features.select_dtypes(include="number").columns.tolist()
    numeric_columns = [column for column in inferred_numeric if column not in forced_categories]
    categorical_columns = [column for column in features.columns if column not in numeric_columns]
    return numeric_columns, categorical_columns


def prepare_categorical_values(features: pd.DataFrame, categorical_columns: list[str]) -> pd.DataFrame:
    """将类别代码统一为字符串；缺失值保留为 np.nan，交给 Pipeline 填补。"""
    prepared = features.copy()
    for column in categorical_columns:
        prepared[column] = prepared[column].map(lambda value: str(value) if pd.notna(value) else np.nan)
    return prepared


def build_preprocessor(numeric_columns: list[str], categorical_columns: list[str]) -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="Missing")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_columns),
            ("categorical", categorical_pipeline, categorical_columns),
        ],
        verbose_feature_names_out=False,
    )


def save_artifacts(
    output_dir: Path,
    preprocessor: ColumnTransformer,
    x_train_processed,
    x_test_processed,
    numeric_columns: list[str],
    categorical_columns: list[str],
    y_train: pd.Series,
    y_test: pd.Series,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # 独热编码后的矩阵大部分是 0，因此以稀疏格式保存，避免浪费磁盘空间。
    sparse.save_npz(output_dir / "x_train.npz", sparse.csr_matrix(x_train_processed))
    sparse.save_npz(output_dir / "x_test.npz", sparse.csr_matrix(x_test_processed))
    joblib.dump(preprocessor, output_dir / "preprocessor.joblib")

    feature_names = preprocessor.get_feature_names_out().tolist()
    with (output_dir / "feature_names.json").open("w", encoding="utf-8") as file:
        json.dump(feature_names, file, ensure_ascii=False, indent=2)

    metadata = {
        "target_column": TARGET_COLUMN,
        "excluded_identifier_columns": IDENTIFIER_COLUMNS,
        "forced_categorical_columns": FORCE_CATEGORICAL_COLUMNS,
        "numeric_feature_count_before_encoding": len(numeric_columns),
        "categorical_feature_count_before_encoding": len(categorical_columns),
        "feature_count_after_preprocessing": len(feature_names),
        "train_samples": len(y_train),
        "test_samples": len(y_test),
        "numeric_preprocessing": ["median imputation", "standard scaling"],
        "categorical_preprocessing": ["constant Missing imputation", "one-hot encoding"],
    }
    with (output_dir / "preprocessing_summary.json").open("w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)


def main() -> None:
    arguments = parse_arguments()
    x_train, y_train = load_features_and_target(arguments.train_path)
    x_test, y_test = load_features_and_target(arguments.test_path)

    numeric_columns, categorical_columns = identify_feature_columns(x_train)
    x_train = prepare_categorical_values(x_train, categorical_columns)
    x_test = prepare_categorical_values(x_test, categorical_columns)

    preprocessor = build_preprocessor(numeric_columns, categorical_columns)
    # 只在训练集上 fit；测试集只能 transform，避免其均值、类别等信息泄漏。
    x_train_processed = preprocessor.fit_transform(x_train)
    x_test_processed = preprocessor.transform(x_test)

    save_artifacts(
        arguments.output_dir,
        preprocessor,
        x_train_processed,
        x_test_processed,
        numeric_columns,
        categorical_columns,
        y_train,
        y_test,
    )

    print("Ames Housing 特征预处理完成")
    print(f"删除标识符：{'、'.join(IDENTIFIER_COLUMNS)}")
    print(f"原始有效特征：数值 {len(numeric_columns)} 个；类别 {len(categorical_columns)} 个")
    print(f"独热编码后特征数：{x_train_processed.shape[1]}")
    print(f"训练集矩阵形状：{x_train_processed.shape}")
    print(f"测试集矩阵形状：{x_test_processed.shape}")
    print(f"预处理产物已保存到：{arguments.output_dir}")


if __name__ == "__main__":
    main()
