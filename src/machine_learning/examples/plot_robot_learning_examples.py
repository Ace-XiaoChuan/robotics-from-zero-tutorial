"""画理想误差递推；不模拟执行器，不训练策略。"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    root = Path(__file__).resolve().parent
    data = json.loads((root / "robot_learning_results.json").read_text())["results"]["18_bias_accumulation"]
    time = [step * data["dt_s"] for step in range(len(data["replay_error_m"]))]
    fig, axis = plt.subplots(figsize=(7, 4), constrained_layout=True)
    axis.plot(time, [1000 * error for error in data["replay_error_m"]], label="Fixed replay: d(next) = d + 1 mm", color="#cc3311")
    axis.plot(time, [1000 * error for error in data["feedback_error_m"]], label="Feedback: d(next) = 0.8 d + 1 mm", color="#4477aa")
    axis.axhline(1000 * data["limit_m"], color="#4477aa", linestyle="--", alpha=0.6, label="Feedback steady limit: 5 mm")
    axis.set(title="Artificial kinematic recurrences - no training or robot execution", xlabel="Time (s), control period 0.1 s", ylabel="Tracking error d = x - reference (mm)")
    axis.grid(alpha=0.2)
    axis.legend(fontsize=8)
    output = root / "robot_learning_error_illustration.png"
    fig.savefig(output, dpi=140)
    plt.close(fig)
    print(output)


if __name__ == "__main__":
    main()
