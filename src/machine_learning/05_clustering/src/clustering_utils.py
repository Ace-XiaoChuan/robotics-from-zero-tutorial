"""第五周聚类项目共享的读取、预处理与输出工具。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler, StandardScaler


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATA_PATH = PROJECT_DIR / "data" / "customer_data.csv"
OUTPUT_DIR = PROJECT_DIR / "outputs"
RANDOM_STATE = 42


class IQRClipper(BaseEstimator, TransformerMixin):
    """以训练数据的 IQR 边界截断异常值；``none`` 时不改变数据。"""

    def __init__(self, enabled: bool = False, factor: float = 1.5) -> None:
        self.enabled = enabled
        self.factor = factor

    def fit(self, x: pd.DataFrame | np.ndarray, y: object = None) -> "IQRClipper":
        values = np.asarray(x, dtype=float)
        self.lower_bounds_ = np.nanpercentile(values, 25, axis=0)
        self.upper_bounds_ = np.nanpercentile(values, 75, axis=0)
        spread = self.upper_bounds_ - self.lower_bounds_
        self.clip_lower_ = self.lower_bounds_ - self.factor * spread
        self.clip_upper_ = self.upper_bounds_ + self.factor * spread
        return self

    def transform(self, x: pd.DataFrame | np.ndarray) -> np.ndarray:
        values = np.asarray(x, dtype=float)
        if not self.enabled:
            return values
        return np.clip(values, self.clip_lower_, self.clip_upper_)


def parse_columns(value: str | None) -> list[str] | None:
    if not value:
        return None
    columns = [item.strip() for item in value.split(",") if item.strip()]
    if not columns:
        raise ValueError("--feature-columns 至少要包含一列。")
    if len(columns) != len(set(columns)):
        raise ValueError("--feature-columns 中存在重复列。")
    return columns


def load_data(data_path: Path) -> pd.DataFrame:
    if not data_path.is_file():
        raise FileNotFoundError(
            f"未找到数据文件：{data_path}。可先运行 src/generate_demo_data.py，"
            "或使用 --data-path 指向自己的 CSV。"
        )
    data = pd.read_csv(data_path)
    if data.empty:
        raise ValueError("数据文件没有任何样本。")
    return data


def choose_feature_columns(
    data: pd.DataFrame, requested_columns: Iterable[str] | None, reference_label_column: str | None
) -> list[str]:
    """选择数值特征；自动模式跳过明显的 ID 列和事后参考类别。"""
    if reference_label_column and reference_label_column not in data.columns:
        raise ValueError(f"未找到真实类别参考列：{reference_label_column}")

    if requested_columns is None:
        candidates = data.select_dtypes(include="number").columns.tolist()
        columns = [
            column
            for column in candidates
            if column != reference_label_column and not column.lower().endswith(("_id", "id", "index"))
        ]
    else:
        columns = list(requested_columns)
        missing = [column for column in columns if column not in data.columns]
        if missing:
            raise ValueError(f"数据缺少指定特征列：{missing}")
        if reference_label_column in columns:
            raise ValueError("真实类别参考列只能事后比较，不能放入 --feature-columns。")

    if len(columns) < 2:
        raise ValueError("聚类至少需要两列数值特征；请用 --feature-columns 明确指定。")
    non_numeric = [column for column in columns if not pd.api.types.is_numeric_dtype(data[column])]
    if non_numeric:
        raise ValueError(f"K-Means 只能直接使用数值列；以下列不是数值型：{non_numeric}")
    all_missing = [column for column in columns if data[column].isna().all()]
    if all_missing:
        raise ValueError(f"以下特征全为空，无法填补：{all_missing}")
    return columns


def build_preprocessor(scaler: str, clip_outliers: bool) -> Pipeline:
    if scaler == "standard":
        scaler_step = StandardScaler()
    elif scaler == "robust":
        scaler_step = RobustScaler()
    else:
        raise ValueError("scaler 只能是 standard 或 robust。")
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("iqr_clipper", IQRClipper(enabled=clip_outliers)),
            ("scaler", scaler_step),
        ]
    )


def iqr_outlier_report(features: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | int | str]] = []
    for column in features.columns:
        series = features[column]
        q1, q3 = series.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        rows.append(
            {
                "feature": column,
                "missing_count": int(series.isna().sum()),
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr),
                "lower_iqr_bound": float(lower),
                "upper_iqr_bound": float(upper),
                "outlier_count": int(((series < lower) | (series > upper)).sum()),
            }
        )
    return pd.DataFrame(rows)


def save_json(path: Path, content: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(content, file, ensure_ascii=False, indent=2)


def ensure_output_directories() -> None:
    for directory in (OUTPUT_DIR / "figures", OUTPUT_DIR / "models", OUTPUT_DIR / "tables"):
        directory.mkdir(parents=True, exist_ok=True)
