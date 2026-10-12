"""画人工构造的训练曲线，不读取或生成模型训练结果。"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


CURVES = [
    ("Both improving", [0.70, 0.50, 0.40, 0.30, 0.25], [0.72, 0.55, 0.46, 0.41, 0.38]),
    ("Validation turns upward", [0.70, 0.45, 0.30, 0.20, 0.12], [0.72, 0.50, 0.43, 0.49, 0.62]),
    ("Both plateau", [0.70, 0.69, 0.69, 0.69, 0.69], [0.71, 0.70, 0.70, 0.70, 0.70]),
    ("Oscillation and growth", [0.70, 1.20, 0.80, 2.00, 4.00], [0.73, 1.10, 0.90, 2.20, 4.30]),
]


def main():
    epochs = [1, 2, 3, 4, 5]
    fig, axes = plt.subplots(2, 2, figsize=(9, 6), constrained_layout=True)
    fig.suptitle("Illustrative loss curves - artificial values, no training run", fontsize=12)
    for axis, (title, training, validation) in zip(axes.flat, CURVES):
        axis.plot(epochs, training, "o-", label="Train")
        axis.plot(epochs, validation, "s--", label="Validation")
        axis.set(title=title, xlabel="Epoch", ylabel="Mean loss", xticks=epochs, ylim=(0, max(training + validation) * 1.12))
        axis.grid(alpha=0.25)
        axis.legend(fontsize=9)
    axes[0, 1].annotate("Minimum validation loss", xy=(3, 0.43), xytext=(2.2, 0.70),
                        arrowprops={"arrowstyle": "->"}, fontsize=8)
    destination = Path(__file__).with_name("training_curves_illustration.png")
    fig.savefig(destination, dpi=140)
    plt.close(fig)
    print(destination)


if __name__ == "__main__":
    main()
