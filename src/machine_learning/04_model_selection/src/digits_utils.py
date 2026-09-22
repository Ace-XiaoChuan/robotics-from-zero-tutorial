"""第 4 周 Digits 工作流程共用的常量和辅助函数。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
MODELS_DIR = OUTPUT_DIR / "models"
TABLES_DIR = OUTPUT_DIR / "tables"

TRAIN_PATH = DATA_DIR / "train_split.csv"
TEST_PATH = DATA_DIR / "test_split.csv"
SPLIT_METADATA_PATH = DATA_DIR / "split_metadata.json"
MODEL_SELECTION_PATH = TABLES_DIR / "model_selection.json"
BEST_PIPELINE_PATH = MODELS_DIR / "best_cross_validated_pipeline.joblib"

RANDOM_STATE = 42
TARGET_COLUMN = "digit"
IDENTIFIER_COLUMN = "sample_index"
FEATURE_COLUMNS = [f"pixel_{row}_{column}" for row in range(8) for column in range(8)]


def ensure_output_directories() -> None:
    """在标准输出目录不存在时创建它们。"""
    for directory in (FIGURES_DIR, MODELS_DIR, TABLES_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def load_split(data_path: Path) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """加载一个已保存的数据划分，并返回特征、标签和原始索引。"""
    if not data_path.is_file():
        raise FileNotFoundError(f"未找到数据切分文件：{data_path}。请先运行 src/split_digits.py。")

    data = pd.read_csv(data_path)
    required_columns = [IDENTIFIER_COLUMN, TARGET_COLUMN, *FEATURE_COLUMNS]
    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(f"数据文件缺少必需字段：{missing_columns}")
    if data[FEATURE_COLUMNS].isna().any().any():
        raise ValueError("Digits 切分文件不应包含缺失像素值。")

    return (
        data[FEATURE_COLUMNS].copy(),
        data[TARGET_COLUMN].astype(int).copy(),
        data[IDENTIFIER_COLUMN].astype(int).copy(),
    )


def build_estimator(candidate: dict[str, Any]) -> Pipeline:
    """根据可序列化的选择配置构建一个候选 Pipeline。"""
    model_family = candidate["model_family"]
    preprocessing = candidate["preprocessing"]
    hyperparameters = candidate["hyperparameters"]

    if model_family == "knn":
        model = KNeighborsClassifier(**hyperparameters)
    elif model_family == "decision_tree":
        model = DecisionTreeClassifier(random_state=RANDOM_STATE, **hyperparameters)
    else:
        raise ValueError(f"未知模型类型：{model_family}")

    steps: list[tuple[str, object]] = []
    if preprocessing == "standard_scaler":
        steps.append(("scaler", StandardScaler()))
    elif preprocessing != "raw_pixels":
        raise ValueError(f"未知预处理方式：{preprocessing}")
    steps.append(("model", model))
    return Pipeline(steps=steps)


def candidate_name(candidate: dict[str, Any]) -> str:
    """返回简洁、便于阅读的候选方案标识。"""
    parameters = ", ".join(f"{key}={value}" for key, value in candidate["hyperparameters"].items())
    return f"{candidate['model_family']} | {candidate['preprocessing']} | {parameters}"


def write_json(data: dict[str, Any], output_path: Path) -> None:
    """以稳定且易读的缩进写入 UTF-8 JSON。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
