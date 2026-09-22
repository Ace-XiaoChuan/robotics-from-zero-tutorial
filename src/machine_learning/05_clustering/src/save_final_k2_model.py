"""保存最终 K=2 客户归属、簇画像、训练配置和可复用模型。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, RobustScaler


PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = PROJECT_DIR / "data" / "wholesale_customers.csv"
REFERENCE_SCALED_PATH = PROJECT_DIR / "outputs" / "tables" / "wholesale_customers_log1p_robust_scaled.csv"
ASSIGNMENTS_PATH = PROJECT_DIR / "outputs" / "tables" / "final_k2_customer_assignments.csv"
PROFILES_PATH = PROJECT_DIR / "outputs" / "tables" / "final_k2_cluster_profiles.csv"
METADATA_PATH = PROJECT_DIR / "outputs" / "tables" / "final_k2_metadata.json"
MODEL_PATH = PROJECT_DIR / "outputs" / "models" / "final_k2_model.joblib"

FEATURES = ["Fresh", "Milk", "Grocery", "Frozen", "Detergents_Paper", "Delicassen"]
SCALED_COLUMNS = [f"{feature}_log1p_robust_scaled" for feature in FEATURES]
CHANNEL_NAMES = {1: "Horeca", 2: "Retail"}
CLUSTER_NAMES = {
    0: "Fresh/Frozen偏高型（以Horeca为主）",
    1: "Milk/Grocery/Detergents_Paper偏高型（以Retail为主）",
}
N_CLUSTERS = 2
RANDOM_STATE = 42
N_INIT = 20


def validate_raw_data(raw: pd.DataFrame) -> None:
    required = ["Channel", "Region", *FEATURES]
    missing_columns = [column for column in required if column not in raw.columns]
    if missing_columns:
        raise ValueError(f"原始数据缺少字段：{missing_columns}")
    if raw[FEATURES].isna().any().any():
        raise ValueError("六个消费特征存在缺失值，不能复现当前无填补流程。")
    if (raw[FEATURES] < 0).any().any():
        raise ValueError("消费特征存在负数，不能直接使用 log1p。")


def build_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("log1p", FunctionTransformer(np.log1p, feature_names_out="one-to-one")),
            # 复现此前“先保存六位小数 log1p CSV，再做 RobustScaler”的学习流程。
            (
                "round_log1p_to_6_decimals",
                FunctionTransformer(np.round, kw_args={"decimals": 6}, feature_names_out="one-to-one"),
            ),
            ("robust_scaler", RobustScaler()),
            (
                "kmeans",
                KMeans(
                    n_clusters=N_CLUSTERS,
                    init="k-means++",
                    n_init=N_INIT,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def rank_labels(raw: pd.DataFrame, original_labels: np.ndarray) -> tuple[np.ndarray, dict[int, int]]:
    """按簇内总消费中位数从低到高，将模型原始编号映射为 C0、C1。"""
    total_spending = raw[FEATURES].sum(axis=1)
    ordered = total_spending.groupby(original_labels).median().sort_values().index
    label_map = {int(original): int(rank) for rank, original in enumerate(ordered)}
    ranked = np.array([label_map[int(label)] for label in original_labels], dtype=int)
    return ranked, label_map


def verify_preprocessing(raw: pd.DataFrame, transformed: np.ndarray) -> float:
    """确认重新拟合的预处理器与此前保存的缩放 CSV 一致。"""
    reference = pd.read_csv(REFERENCE_SCALED_PATH)
    if len(reference) != len(raw):
        raise ValueError("缩放参考数据与原始数据的客户数不一致。")
    if not np.array_equal(reference["customer_row"].to_numpy(), np.arange(1, len(raw) + 1)):
        raise ValueError("缩放参考数据的 customer_row 顺序不一致。")
    difference = np.abs(reference[SCALED_COLUMNS].to_numpy() - transformed)
    max_difference = float(difference.max())
    if max_difference > 1e-6:
        raise ValueError(f"重新拟合的预处理结果与缩放 CSV 不一致，最大差值为 {max_difference:.8g}。")
    return max_difference


def build_assignments(raw: pd.DataFrame, ranked_labels: np.ndarray) -> pd.DataFrame:
    assignments = raw.copy()
    assignments.insert(0, "customer_row", np.arange(1, len(raw) + 1))
    assignments["cluster"] = [f"C{label}" for label in ranked_labels]
    assignments["cluster_name"] = [CLUSTER_NAMES[int(label)] for label in ranked_labels]
    return assignments


def build_profiles(raw: pd.DataFrame, ranked_labels: np.ndarray) -> pd.DataFrame:
    overall_medians = raw[FEATURES].median()
    total_spending = raw[FEATURES].sum(axis=1)
    rows: list[dict[str, int | float | str]] = []
    for cluster in range(N_CLUSTERS):
        mask = ranked_labels == cluster
        subset = raw.loc[mask]
        channel_counts = subset["Channel"].value_counts()
        row: dict[str, int | float | str] = {
            "cluster": f"C{cluster}",
            "cluster_name": CLUSTER_NAMES[cluster],
            "sample_count": int(mask.sum()),
            "sample_share": float(mask.mean()),
            "median_total_annual_spending": float(total_spending.loc[mask].median()),
            "horeca_count": int(channel_counts.get(1, 0)),
            "horeca_percentage": float(channel_counts.get(1, 0) / mask.sum() * 100),
            "retail_count": int(channel_counts.get(2, 0)),
            "retail_percentage": float(channel_counts.get(2, 0) / mask.sum() * 100),
        }
        for feature in FEATURES:
            row[f"{feature}_median"] = float(subset[feature].median())
            row[f"{feature}_mean"] = float(subset[feature].mean())
            row[f"{feature}_median_vs_overall"] = float(subset[feature].median() / overall_medians[feature])
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    raw = pd.read_csv(RAW_DATA_PATH)
    validate_raw_data(raw)

    pipeline = build_pipeline()
    original_labels = pipeline.fit_predict(raw[FEATURES])
    transformed = pipeline[:-1].transform(raw[FEATURES])
    max_preprocessing_difference = verify_preprocessing(raw, transformed)
    ranked_labels, label_map = rank_labels(raw, original_labels)

    assignments = build_assignments(raw, ranked_labels)
    profiles = build_profiles(raw, ranked_labels)
    silhouette = float(silhouette_score(transformed, original_labels))
    kmeans = pipeline.named_steps["kmeans"]

    ASSIGNMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    assignments.to_csv(ASSIGNMENTS_PATH, index=False)
    profiles.to_csv(PROFILES_PATH, index=False, float_format="%.3f")

    model_bundle = {
        "pipeline": pipeline,
        "feature_columns": FEATURES,
        "label_map_original_to_ranked": label_map,
        "cluster_names": CLUSTER_NAMES,
        "channel_names_for_posthoc_reference": CHANNEL_NAMES,
        "notes": "Channel and Region are excluded from preprocessing and K-Means.",
    }
    joblib.dump(model_bundle, MODEL_PATH)

    metadata = {
        "saved_on": date.today().isoformat(),
        "data_path": str(RAW_DATA_PATH.relative_to(PROJECT_DIR)),
        "sample_count": len(raw),
        "feature_columns": FEATURES,
        "excluded_reference_columns": ["Channel", "Region"],
        "missing_value_count": int(raw[FEATURES].isna().sum().sum()),
        "outlier_clipping": False,
        "preprocessing": [
            "numpy.log1p",
            "round log1p values to 6 decimals (reproduces saved intermediate CSV)",
            "sklearn.preprocessing.RobustScaler",
        ],
        "n_clusters": N_CLUSTERS,
        "kmeans_parameters": {
            "init": "k-means++",
            "n_init": N_INIT,
            "random_state": RANDOM_STATE,
        },
        "label_order": "cluster median total annual spending, low to high",
        "label_map_original_to_ranked": {str(key): value for key, value in label_map.items()},
        "cluster_names": {f"C{key}": value for key, value in CLUSTER_NAMES.items()},
        "cluster_sizes": {
            f"C{cluster}": int((ranked_labels == cluster).sum()) for cluster in range(N_CLUSTERS)
        },
        "inertia": float(kmeans.inertia_),
        "silhouette_score": silhouette,
        "n_iter": int(kmeans.n_iter_),
        "preprocessing_verification_max_abs_difference": max_preprocessing_difference,
        "software_versions": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
        "artifacts": {
            "assignments": str(ASSIGNMENTS_PATH.relative_to(PROJECT_DIR)),
            "profiles": str(PROFILES_PATH.relative_to(PROJECT_DIR)),
            "model": str(MODEL_PATH.relative_to(PROJECT_DIR)),
        },
        "interpretation_warning": (
            "Cluster names are exploratory descriptions. Channel was used only for post-hoc interpretation, "
            "not as a training label or accuracy target."
        ),
    }
    with METADATA_PATH.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)

    print("最终 K=2 结果已保存")
    print(f"客户归属：{ASSIGNMENTS_PATH}")
    print(f"最终画像：{PROFILES_PATH}")
    print(f"模型包：{MODEL_PATH}")
    print(f"训练记录：{METADATA_PATH}")
    print(f"簇规模：{metadata['cluster_sizes']}")
    print(f"inertia={kmeans.inertia_:.6f}；silhouette={silhouette:.6f}；迭代次数={kmeans.n_iter_}")
    print(f"预处理复核最大绝对误差：{max_preprocessing_difference:.2e}")


if __name__ == "__main__":
    main()
