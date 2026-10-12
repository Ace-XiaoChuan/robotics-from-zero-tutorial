"""绘制 12/17 的人工视觉输出与解析轨迹；不调用学习模型。"""

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle


ROOT = Path(__file__).resolve().parents[1]


def cup_polygon(left):
    return [(left, 140), (left + 100, 140), (left + 90, 290),
            (left + 80, 300), (left + 20, 300), (left + 10, 290)]


def plot_vision():
    fig, axes = plt.subplots(1, 4, figsize=(12, 3.4), constrained_layout=True)
    fig.suptitle("Same artificial scene, different output contracts - no model inference", fontsize=11)
    titles = ["Classification", "Detection", "Instance masks", "Semantic keypoints"]
    for index, (axis, title) in enumerate(zip(axes, titles)):
        axis.set(xlim=(0, 640), ylim=(480, 0), title=title, xlabel="u (px)")
        axis.set_aspect("equal")
        axis.set_yticks([0, 240, 480])
        axis.add_patch(Rectangle((0, 340), 640, 140, facecolor="#ece6dc", edgecolor="none"))
        for object_id, (left, color) in enumerate(((120, "#d95555"), (380, "#5188cf")), 1):
            fill = color if index != 2 else ("#4da78a" if object_id == 1 else "#af80d2")
            axis.add_patch(Polygon(cup_polygon(left), closed=True, facecolor=fill, edgecolor="#333333", linewidth=1))
            if index == 1:
                axis.add_patch(Rectangle((left, 140), 100, 160, fill=False, edgecolor=color, linewidth=2, linestyle="--"))
                axis.text(left, 125, "cup", fontsize=8)
            elif index == 2:
                axis.text(left + 50, 220, f"ID {object_id}", ha="center", fontsize=8, color="white")
            elif index == 3:
                axis.scatter([left + 50, left + 50], [150, 290], s=35, color="#f5cc45", edgecolors="black", zorder=3)
        if index == 0:
            axis.text(320, 70, "cup, red, blue", ha="center", fontsize=9)
    axes[0].set_ylabel("v (px), downward")
    output = ROOT / "12_detection_segmentation/vision_outputs_illustration.png"
    fig.savefig(output, dpi=140)
    plt.close(fig)
    print(output)


def plot_trajectories():
    theta = [math.pi * (1 - i / 400) for i in range(401)]
    x = [math.cos(value) for value in theta]
    upper = [math.sin(value) for value in theta]
    lower = [-value for value in upper]
    fig, axis = plt.subplots(figsize=(6.5, 4.5), constrained_layout=True)
    axis.add_patch(Circle((0, 0), 0.25, facecolor="#bbbbbb", edgecolor="#555555", label="Obstacle, r=0.25 m"))
    axis.plot(x, upper, label="Upper feasible path", color="#4477aa", linewidth=2)
    axis.plot(x, lower, label="Lower feasible path", color="#228833", linewidth=2)
    axis.plot(x, [0] * len(x), "--", color="#cc3311", linewidth=2, label="Pointwise mean: collision")
    axis.scatter([-1, 1], [0, 0], color="black", zorder=3)
    axis.annotate("Start", (-1, 0), xytext=(-1.22, 0.1), fontsize=9)
    axis.annotate("Goal", (1, 0), xytext=(1.04, 0.1), fontsize=9)
    axis.set(title="Artificial point trajectories - no robot execution", xlabel="base x (m)", ylabel="base y (m)",
             xlim=(-1.3, 1.35), ylim=(-1.2, 1.2))
    axis.set_aspect("equal")
    axis.grid(alpha=0.2)
    axis.legend(fontsize=8, loc="upper right")
    output = ROOT / "17_generative_models/trajectory_modes_illustration.png"
    fig.savefig(output, dpi=140)
    plt.close(fig)
    print(output)


if __name__ == "__main__":
    plot_vision()
    plot_trajectories()
