"""用合成测量和独立标签演示统计估计、预测区间与概率校准。"""

import argparse
import json
from pathlib import Path
import platform
from statistics import NormalDist

import numpy as np


TRUE_POSITION_M = 0.50
KNOWN_SIGMA_M = 0.02
SAMPLE_SIZES = (10, 100, 1000)
Z95 = NormalDist().inv_cdf(0.975)
RAW_PROBABILITIES = np.array([0.6, 0.9])
TRUE_GROUP_PROBABILITIES = np.array([0.6, 0.8])


def interval_half_widths(n, sigma):
    """独立高斯测量、已知总体标准差：均值 CI 和下一读数 PI 的半宽。"""
    if n < 1 or not np.isfinite(sigma) or sigma <= 0:
        raise ValueError("n 必须为正，sigma 必须为有限正数")
    mean_se = sigma / np.sqrt(n)
    prediction_se = np.sqrt(sigma**2 + mean_se**2)
    return float(Z95 * mean_se), float(Z95 * prediction_se)


def summarize_measurements(readings, sigma):
    readings = np.asarray(readings, dtype=float)
    if readings.ndim != 1 or len(readings) < 2 or not np.all(np.isfinite(readings)):
        raise ValueError("至少需要两个有限的一维测量值")
    n = len(readings)
    mean = float(readings.mean())
    ci_half, pi_half = interval_half_widths(n, sigma)
    return {
        "n": n,
        "sample_mean_m": mean,
        "sample_variance_m2": float(readings.var(ddof=1)),
        "sample_std_m": float(readings.std(ddof=1)),
        # 区间使用已知 sigma，样本标准差只作描述统计。
        "mean_standard_error_m": float(sigma / np.sqrt(n)),
        "mean_ci95_m": [mean - ci_half, mean + ci_half],
        "next_reading_pi95_m": [mean - pi_half, mean + pi_half],
        "mean_ci95_half_width_m": ci_half,
        "next_reading_pi95_half_width_m": pi_half,
    }


def repeated_coverage(n, repeats, seed, shift_m=0.06):
    """每轮重新采 n 次、估计均值，再采一个独立的新读数；不在拟合数据上评估。"""
    if repeats < 2:
        raise ValueError("至少需要重复两轮")
    rng = np.random.default_rng(seed)
    # [重复轮数, 每轮测量数]；每行是一组独立实验。
    readings = rng.normal(TRUE_POSITION_M, KNOWN_SIGMA_M, (repeats, n))
    estimates = readings.mean(axis=1)
    future = rng.normal(TRUE_POSITION_M, KNOWN_SIGMA_M, repeats)
    # 相同的新噪声叠加固定偏移，比较条件变化前后同一批区间。
    shifted_future = future + shift_m
    ci_half, pi_half = interval_half_widths(n, KNOWN_SIGMA_M)
    counts = {
        "mean_ci_contains_truth": int(np.count_nonzero(
            np.abs(estimates - TRUE_POSITION_M) <= ci_half)),
        "prediction_pi_contains_future": int(np.count_nonzero(
            np.abs(future - estimates) <= pi_half)),
        "wrong_mean_ci_contains_future": int(np.count_nonzero(
            np.abs(future - estimates) <= ci_half)),
        "old_prediction_pi_contains_shifted_future": int(np.count_nonzero(
            np.abs(shifted_future - estimates) <= pi_half)),
    }
    return {
        "n": n, "repeats": repeats, "seed": seed,
        "mean_estimates_std_m": float(estimates.std(ddof=1)),
        "future_readings_std_m": float(future.std(ddof=1)),
        "counts": counts,
        "coverage": {name: count / repeats for name, count in counts.items()},
    }


def probability_metrics(probabilities, labels):
    """probabilities 为 [组数]，labels 为 [组数, 每组样本数]。"""
    probabilities = np.asarray(probabilities, dtype=float)
    labels = np.asarray(labels)
    if (probabilities.ndim != 1 or labels.ndim != 2
            or labels.shape[0] != len(probabilities) or labels.shape[1] == 0
            or not np.all(np.isfinite(probabilities))
            or np.any((probabilities < 0) | (probabilities > 1))
            or not np.all((labels == 0) | (labels == 1))):
        raise ValueError("需要 [0,1] 概率和对应的非空二分类标签矩阵")
    p = probabilities[:, None]  # [组数, 1]，广播到每组的所有样本。
    clipped = np.clip(p, 1e-12, 1 - 1e-12)
    return {
        "accuracy_at_0_5": float(np.mean((p >= 0.5) == labels)),
        "brier_score": float(np.mean((p - labels)**2)),
        "mean_nll": float(-np.mean(
            labels * np.log(clipped) + (1 - labels) * np.log(1 - clipped))),
    }


def calibration_study(seed, calibration_n=200, evaluation_n=5000):
    # 分别抽取校准集和评估集；校准器只能读取第一组标签。
    calibration_rng = np.random.default_rng(seed)
    evaluation_rng = np.random.default_rng(seed + 1)
    calibration_labels = (
        calibration_rng.random((2, calibration_n)) < TRUE_GROUP_PROBABILITIES[:, None]
    ).astype(int)
    evaluation_labels = (
        evaluation_rng.random((2, evaluation_n)) < TRUE_GROUP_PROBABILITIES[:, None]
    ).astype(int)
    calibrated = calibration_labels.mean(axis=1)
    observed = evaluation_labels.mean(axis=1)
    return {
        "raw_probabilities": RAW_PROBABILITIES.tolist(),
        "true_group_probabilities": TRUE_GROUP_PROBABILITIES.tolist(),
        "calibration_seed": seed, "evaluation_seed": seed + 1,
        "calibration_n_per_group": calibration_n,
        "evaluation_n_per_group": evaluation_n,
        "calibration_positive_counts": calibration_labels.sum(axis=1).tolist(),
        "evaluation_positive_counts": evaluation_labels.sum(axis=1).tolist(),
        "calibrated_probabilities": calibrated.tolist(),
        "evaluation_positive_fractions": observed.tolist(),
        "raw_metrics": probability_metrics(RAW_PROBABILITIES, evaluation_labels),
        "calibrated_metrics": probability_metrics(calibrated, evaluation_labels),
    }


def plot_results(output, readings, summaries, coverage_rows, calibration):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 英文图中文字避免额外字体依赖；中文阅读方法放在 practice.md。
    blue, orange, red = "#2463a0", "#dc8423", "#b74242"
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.3), constrained_layout=True)
    ax = axes[0]
    ax.scatter(np.arange(1, 61), readings[:60] * 1000, s=15, color=blue)
    ax.axhline(TRUE_POSITION_M * 1000, color="black", linestyle="--", label="true position")
    ax.set(xlabel="Measurement index (object is stationary)", ylabel="Position (mm)",
           title="A. Individual readings keep fluctuating")
    ax.legend(fontsize=8)

    ax = axes[1]
    for i, row in enumerate(summaries):
        mean = row["sample_mean_m"] * 1000
        ax.errorbar(mean, i + 0.10, xerr=row["next_reading_pi95_half_width_m"] * 1000,
                    fmt="o", capsize=5, color=orange, label="95% next-reading PI" if i == 0 else None)
        ax.errorbar(mean, i - 0.10, xerr=row["mean_ci95_half_width_m"] * 1000,
                    fmt="o", capsize=5, color=blue, label="95% mean CI" if i == 0 else None)
    ax.axvline(TRUE_POSITION_M * 1000, color="black", linestyle="--")
    ax.set(yticks=range(len(summaries)), yticklabels=[f"n={r['n']}" for r in summaries],
           xlabel="Position (mm)", title="B. Two intervals answer different questions")
    ax.invert_yaxis()
    ax.legend(fontsize=8, loc="upper right", bbox_to_anchor=(1, .82))

    ax = axes[2]
    curves = [
        ("mean_ci_contains_truth", "Mean CI covers true position", blue, "o-"),
        ("prediction_pi_contains_future", "Prediction PI covers new reading", orange, "s-"),
        ("wrong_mean_ci_contains_future", "Wrong: mean CI used for new reading", "#777777", "^-"),
        ("old_prediction_pi_contains_shifted_future", "Old PI after +60 mm bias", red, "x--"),
    ]
    for key, label, color, style in curves:
        ax.plot([r["n"] for r in coverage_rows],
                [r["coverage"][key] * 100 for r in coverage_rows], style,
                color=color, label=label)
    ax.axhline(95, color="black", linewidth=.7, linestyle=":")
    ax.set(xscale="log", xlabel="Measurements per independent experiment",
           ylabel="Empirical coverage (%)", ylim=(0, 101),
           title=f"C. {coverage_rows[0]['repeats']:,} repeated experiments")
    ax.legend(fontsize=7, loc="center left")
    for ax in axes:
        ax.grid(alpha=.2)
    fig.suptitle("Synthetic Gaussian measurements; known noise SD = 20 mm")
    fig.savefig(output / "figures" / "measurement_uncertainty.png", dpi=150)
    plt.close(fig)

    raw = np.array(calibration["raw_probabilities"])
    calibrated = np.array(calibration["calibrated_probabilities"])
    observed = np.array(calibration["evaluation_positive_fractions"])
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
    ax = axes[0]
    ax.plot([0, 1], [0, 1], "--", color="gray", label="perfect calibration")
    ax.plot(raw, observed, "o-", color=red, label="raw scores")
    ax.plot(calibrated, observed, "s-", color=blue, label="fitted on separate calibration labels")
    ax.set(xlabel="Reported positive probability", ylabel="Positive fraction in evaluation labels",
           xlim=(0, 1), ylim=(0, 1), title="A. Reliability diagram (two score groups)")
    ax.legend(fontsize=8)
    ax = axes[1]
    positions = np.arange(2)
    for offset, values, color, label in [
        (-.24, raw, red, "raw score"), (0, calibrated, blue, "calibrated probability"),
        (.24, observed, orange, "independent evaluation frequency"),
    ]:
        ax.bar(positions + offset, values, width=.24, color=color, label=label)
    ax.set(xticks=positions, xticklabels=["raw score 0.6", "raw score 0.9"],
           ylim=(0, 1), ylabel="Probability / frequency", title="B. Prediction versus held-out frequency")
    ax.legend(fontsize=8)
    for ax in axes:
        ax.grid(alpha=.2)
    fig.suptitle("Synthetic scores; 200 calibration and 5,000 evaluation labels per group")
    fig.savefig(output / "figures" / "probability_calibration.png", dpi=150)
    plt.close(fig)
    return matplotlib.__version__


def run(output, seed, repeats):
    output = Path(output)
    (output / "figures").mkdir(parents=True, exist_ok=True)
    (output / "tables").mkdir(parents=True, exist_ok=True)
    readings = np.random.default_rng(seed).normal(TRUE_POSITION_M, KNOWN_SIGMA_M, max(SAMPLE_SIZES))
    summaries = [summarize_measurements(readings[:n], KNOWN_SIGMA_M) for n in SAMPLE_SIZES]
    coverage_rows = [repeated_coverage(n, repeats, seed + 10 + i) for i, n in enumerate(SAMPLE_SIZES)]
    calibration = calibration_study(seed + 100)
    matplotlib_version = plot_results(output, readings, summaries, coverage_rows, calibration)
    report = {
        "environment": {"python": platform.python_version(), "numpy": np.__version__,
                        "matplotlib": matplotlib_version},
        "config": {"seed": seed, "true_position_m": TRUE_POSITION_M,
                   "known_sigma_m": KNOWN_SIGMA_M, "confidence_level": 0.95,
                   "z95": Z95, "sample_sizes": list(SAMPLE_SIZES),
                   "coverage_repeats": repeats, "future_sensor_bias_m": 0.06,
                   "single_sample_subsets": "first n readings from one 1000-reading pool"},
        "probability": {
            "within_one_sigma_theoretical": NormalDist().cdf(1) - NormalDist().cdf(-1),
            "within_one_sigma_observed": float(np.mean(np.abs(readings - TRUE_POSITION_M) <= KNOWN_SIGMA_M)),
            "readings_n": len(readings),
        },
        "single_sample_summaries": summaries,
        "repeated_coverage": coverage_rows,
        "calibration": calibration,
    }
    (output / "tables" / "results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for row, coverage in zip(summaries, coverage_rows):
        print(f"n={row['n']:4d}: mean={row['sample_mean_m']:.6f} m, "
              f"sample SD={row['sample_std_m'] * 1000:.2f} mm, "
              f"CI half-width={row['mean_ci95_half_width_m'] * 1000:.2f} mm, "
              f"PI half-width={row['next_reading_pi95_half_width_m'] * 1000:.2f} mm, "
              f"PI coverage={coverage['coverage']['prediction_pi_contains_future']:.2%}")
    for name in ("raw_metrics", "calibrated_metrics"):
        print(name, json.dumps(calibration[name]))
    print(f"结果已保存：{output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "outputs")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--repeats", type=int, default=5000)
    args = parser.parse_args()
    if args.seed < 0 or args.repeats < 2:
        parser.error("seed 必须非负，repeats 至少为 2")
    run(args.output, args.seed, args.repeats)
