"""Small synthetic capacity study; NumPy solver, no external data or sklearn."""
import argparse
import json
from pathlib import Path
import platform

import numpy as np

SIGMA = 0.2
CONFIGS = [("linear", 1, 0.0), ("cubic", 3, 0.0),
           ("degree12", 12, 0.0), ("ridge12", 12, 0.001),
           ("strong_ridge12", 12, 1.0)]


def truth(x):
    return np.sin(np.pi * x)


def sample(n, seed):
    rng = np.random.default_rng(seed)
    x = rng.uniform(-1, 1, n)
    return x, truth(x) + rng.normal(0, SIGMA, n)


def features(x, degree):
    return np.asarray(x)[:, None] ** np.arange(1, degree + 1)


def fit(x, y, degree, strength):
    """Minimize mean squared residual + strength * ||w||²; free intercept.

    Features x...x**degree are standardized using training statistics only.
    Augmented least squares avoids explicitly inverting a Gram matrix.
    """
    if strength < 0:
        raise ValueError("strength must be nonnegative")
    raw = features(x, degree)
    mean, scale = raw.mean(0), raw.std(0)
    scale = np.where(scale > 0, scale, 1.0)
    design = np.column_stack((np.ones(len(x)), (raw - mean) / scale))
    penalty = np.diag([0.0] + [np.sqrt(len(x) * strength)] * degree)
    coef = np.linalg.lstsq(np.vstack((design, penalty)),
                           np.r_[y, np.zeros(degree + 1)], rcond=None)[0]
    return {"mean": mean, "scale": scale, "coef": coef, "degree": degree}


def predict(model, x):
    z = (features(x, model["degree"]) - model["mean"]) / model["scale"]
    return model["coef"][0] + z @ model["coef"][1:]


def mse(a, b):
    return float(np.mean((a - b) ** 2))


def study(output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    output.mkdir(parents=True, exist_ok=True)
    x, y = sample(20, 42)
    vx, vy = sample(2000, 2026)
    grid = np.linspace(-1, 1, 600)
    single, models = [], {}
    for name, degree, strength in CONFIGS:
        model = fit(x, y, degree, strength)
        models[name] = model
        single.append(dict(name=name, degree=degree, strength=strength,
                           train_mse=mse(y, predict(model, x)),
                           validation_mse=mse(vy, predict(model, vx))))
    repeats = []
    for n in (20, 80, 320):
        values = {name: [] for name, _, _ in CONFIGS[:4]}
        for seed in range(100, 130):
            # Same 320-point pool per seed; nested training subsets as n grows.
            tx, ty = sample(320, seed)
            for name, degree, strength in CONFIGS[:4]:
                model = fit(tx[:n], ty[:n], degree, strength)
                values[name].append([mse(ty[:n], predict(model, tx[:n])),
                                     mse(vy, predict(model, vx))])
        for name, scores in values.items():
            arr = np.asarray(scores)
            repeats.append(dict(n=n, name=name, train_mean=float(arr[:, 0].mean()),
                                validation_mean=float(arr[:, 1].mean()),
                                validation_median=float(np.median(arr[:, 1])),
                                validation_std=float(arr[:, 1].std(ddof=1)),
                                runs=scores))
    report = dict(python=platform.python_version(), numpy=np.__version__,
                  matplotlib=matplotlib.__version__, sigma=SIGMA,
                  training_seed=42, validation_seed=2026, validation_n=2000,
                  repeat_seeds=list(range(100, 130)), single=single, learning=repeats)
    (output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    panels = [("linear", "cubic"), ("degree12",), ("ridge12", "strong_ridge12")]
    for ax, names in zip(axes, panels):
        ax.scatter(x, y, s=16, c="black", label="20 noisy observations", zorder=3)
        ax.plot(grid, truth(grid), "--", color="gray", label="true mean sin(pi*x)")
        for name in names:
            ax.plot(grid, predict(models[name], grid), label=name)
        ax.set(xlabel="x (dimensionless)", ylim=(-2, 2), title=" / ".join(names))
        ax.grid(alpha=.2)
        ax.legend(fontsize=7)
    axes[0].set_ylabel("y (dimensionless)")
    fig.suptitle("Same training data; display clipped to [-2, 2], metrics are not clipped")
    fig.tight_layout()
    fig.savefig(output / "fits.png", dpi=150)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    for name, _, _ in CONFIGS[:4]:
        rows = [row for row in repeats if row["name"] == name]
        for ax, metric in zip(axes, ("train_mean", "validation_mean")):
            ax.plot([r["n"] for r in rows], [r[metric] for r in rows], "o-", label=name)
    for ax, title in zip(axes, ("Mean training MSE", "Mean validation MSE")):
        ax.axhline(SIGMA**2, linestyle="--", color="gray", label="noise variance 0.04")
        ax.set(xscale="log", yscale="log", xlabel="Training observations", ylabel="MSE", title=title)
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
    fig.suptitle("30 training draws; one shared independent validation set; log axes")
    fig.tight_layout()
    fig.savefig(output / "learning.png", dpi=150)
    plt.close(fig)
    print(json.dumps({"single": single, "learning": [{k:v for k,v in row.items() if k != "runs"} for row in repeats]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "results")
    study(parser.parse_args().output)
