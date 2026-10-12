"""核对 09～11 的人工例子与解析解；不调用 ML 库或训练真实模型。"""

import itertools
import json
import math
import platform


def close(actual, expected, *, tolerance=1e-9):
    if not math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance):
        raise AssertionError(f"{actual} != {expected}")


def mean(values):
    return sum(values) / len(values)


def sigmoid(value):
    if value >= 0:
        return 1 / (1 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1 + exp_value)


def binary_loss(logit, label):
    # log(1+exp(z)) 的数值稳定形式。
    return max(logit, 0) + math.log1p(math.exp(-abs(logit))) - label * logit


def entropy(probabilities):
    if any(p < 0 for p in probabilities):
        raise ValueError("概率不能为负")
    close(sum(probabilities), 1)
    return -sum(p * math.log(p) for p in probabilities if p > 0)


def difference(function, value, step=1e-6):
    return (function(value + step) - function(value - step)) / (2 * step)


def gini(labels):
    return 1 - sum((labels.count(value) / len(labels)) ** 2 for value in set(labels))


def main():
    results = {}

    # 09：贝叶斯结果与独立计数相符，先验赔率调整产生相同后验。
    bayes_rows = []
    for prior, positives, false_positives in ((0.5, 450, 50), (0.1, 90, 90), (0.01, 9, 99)):
        posterior = 0.9 * prior / (0.9 * prior + 0.1 * (1 - prior))
        close(posterior, positives / (positives + false_positives))
        old_odds = 0.9 / (1 - 0.9)
        new_odds = old_odds * prior / (1 - prior)  # 旧先验为 0.5。
        close(new_odds / (1 + new_odds), posterior)
        bayes_rows.append({"prior": prior, "posterior": posterior, "tp_fp": [positives, false_positives]})
    results["bayes_prior_shift"] = bayes_rows

    values, probabilities = [0.48, 0.5, 0.52], [0.25, 0.5, 0.25]
    expectation = sum(x * p for x, p in zip(values, probabilities))
    variance = sum(p * (x - expectation) ** 2 for x, p in zip(values, probabilities))
    close(expectation, 0.5)
    close(variance, 0.0002)
    close(sum(p * x * x for x, p in zip(values, probabilities)) - expectation**2, variance)
    std = math.sqrt(variance)
    coverage = sum(p for x, p in zip(values, probabilities) if abs(x - expectation) <= std)
    close(coverage, 0.5)
    # 90 度旋转后，x 方向的方差转到 y 方向，平移不影响协方差。
    points = [(0, x + 1, 2) for x in values]
    center = [sum(p * point[j] for p, point in zip(probabilities, points)) for j in range(3)]
    covariance = [[sum(p * (q[i] - center[i]) * (q[j] - center[j])
                       for p, q in zip(probabilities, points)) for j in range(3)] for i in range(3)]
    close(covariance[1][1], variance)
    close(sum(covariance[i][i] for i in range(3)), variance)
    results["position_moments"] = {"mean_m": expectation, "variance_m2": variance,
                                   "std_m": std, "one_std_coverage": coverage, "rotated_covariance_m2": covariance}

    labels = [1, 1, 1, 0]
    likelihood = lambda p: math.prod(p if y else 1 - p for y in labels)
    nll = lambda p: -math.log(likelihood(p))
    close(difference(nll, 0.75), 0, tolerance=1e-7)
    for p in (0.1, 0.5, 0.74, 0.76, 0.9):
        assert nll(p) > nll(0.75)
    close(mean([binary_loss(math.log(3), y) for y in labels]), nll(0.75) / 4)
    results["bernoulli_likelihood"] = {"mle": 0.75, "likelihood_half": likelihood(0.5),
                                       "likelihood_mle": likelihood(0.75), "mean_nll_mle": nll(0.75) / 4}

    group_labels = [1] * 80 + [0] * 20
    brier = lambda p: mean([(p - y) ** 2 for y in group_labels])
    close(brier(0.9), 0.17)
    close(brier(0.8), 0.16)
    close(difference(brier, 0.8), 0, tolerance=1e-7)
    for delta in (-0.1, -0.01, 0.01, 0.1):
        close(brier(0.8 + delta) - brier(0.8), delta**2)
    results["calibration_brier"] = {"group_count": 100, "positive_frequency": 0.8,
                                     "brier_original": brier(0.9), "brier_group_frequency": brier(0.8),
                                     "two_group_accuracy_at_half": 0.7}

    entropies = [entropy([p, 1 - p]) for p in (0.5, 0.9, 0.99)]
    assert entropies[0] > entropies[1] > entropies[2]
    close(entropy([0, 1]), 0)
    disagreement = entropy([0.5, 0.5]) - mean([entropy([0.1, 0.9]), entropy([0.9, 0.1])])
    close(disagreement, 0.3680642071684971)
    results["entropy_disagreement"] = {"entropy_nats": entropies, "disagreement_nats": disagreement,
                                        "identical_model_disagreement_nats": 0}

    # 10：原始两特征的凸目标驻点，与交互特征的表达区别。
    xs, ys = [(-1, -1), (-1, 1), (1, -1), (1, 1)], [0, 1, 1, 0]
    ts = [2 * y - 1 for y in ys]
    logistic = lambda params: mean([binary_loss(params[0] * x[0] + params[1] * x[1] + params[2], y)
                                    for x, y in zip(xs, ys)]) + 0.5 * (params[0]**2 + params[1]**2)
    for j in range(3):
        def varying(value):
            params = [0, 0, 0]
            params[j] = value
            return logistic(params)
        close(difference(varying, 0), 0)
    for params in itertools.product((-1, 0, 1), repeat=3):
        assert logistic(params) >= logistic((0, 0, 0)) - 1e-12
    interaction_probabilities = [sigmoid(-2 * x[0] * x[1]) for x in xs]
    assert [int(p > 0.5) for p in interaction_probabilities] == ys
    results["logistic_xor"] = {"stationary_parameters": [0, 0, 0], "loss": logistic((0, 0, 0)),
                                "interaction_probabilities": interaction_probabilities}

    hinge = lambda params: 0.5 * (params[0]**2 + params[1]**2) + mean([
        max(0, 1 - t * (params[0] * x[0] + params[1] * x[1] + params[2])) for x, t in zip(xs, ts)])
    close(hinge((0, 0, 0)), 1)
    for j in range(3):
        def varying(value):
            params = [0, 0, 0]
            params[j] = value
            return hinge(params)
        close(difference(varying, 0), 0)
    for params in itertools.product((-2, -0.5, 0, 0.5, 2), repeat=3):
        assert hinge(params) >= 1 - 1e-12
    close(hinge((0, 0, 0.5)), 1)
    results["linear_svm_hinge"] = {"stationary_loss": 1, "example_hinge_losses": [1.5, 0.8, 0]}

    kernel = lambda x, q: math.exp(-0.5 * sum((a - b)**2 for a, b in zip(x, q)))
    alpha = 1 / (1 - math.exp(-2))**2
    score = lambda q: sum(alpha * t * kernel(x, q) for x, t in zip(xs, ts))
    margins = [t * score(x) for x, t in zip(xs, ts)]
    assert 0 < alpha < 2
    close(sum(alpha * t for t in ts), 0)
    for margin in margins:
        close(margin, 1)
    norm_squared = sum(alpha**2 * ti * tj * kernel(xi, xj)
                       for xi, ti in zip(xs, ts) for xj, tj in zip(xs, ts))
    primal = 0.5 * norm_squared + 2 * sum(max(0, 1 - margin) for margin in margins)
    dual = 4 * alpha - 0.5 * norm_squared
    close(primal, dual)  # 零对偶间隙与可行性，而不是只检查预测符号。
    for value in (-2, -0.2, 0, 0.2, 2):
        close(score((0, value)), 0)
        close(score((value, 0)), 0)
    results["rbf_svm_optimality"] = {"alpha": alpha, "C": 2, "gamma": 0.5, "training_margins": margins,
                                      "primal_dual_gap": primal - dual, "query_score": score((-0.8, 0.8))}

    tree = lambda q: int((q[0] <= 0) != (q[1] <= 0))
    close(gini(ys), 0.5)
    splits = []
    for axis in (0, 1):
        groups = [[i for i, x in enumerate(xs) if (x[axis] <= 0) == left] for left in (True, False)]
        weighted_gini = sum(len(group) / len(xs) * gini([ys[i] for i in group]) for group in groups)
        close(weighted_gini, 0.5)
        splits.append({"axis": axis, "gini_improvement": gini(ys) - weighted_gini})
    assert [tree(x) for x in xs] == ys
    results["tree_xor_gini"] = {"root_gini": gini(ys), "first_splits": splits, "manual_tree_predictions": ys}

    averaged = lambda q: (tree(q) + tree((q[1], q[0])) + 0) / 3
    close(averaged(xs[1]), 2 / 3)
    mixed_probabilities = [0.51, 0.51, 0]
    assert sum(p > 0.5 for p in mixed_probabilities) == 2
    close(mean(mixed_probabilities), 0.34)
    results["forest_aggregation"] = {"manual_pure_tree_probability_B": averaged(xs[1]),
                                      "mixed_leaf_hard_vote": 1, "mixed_leaf_mean_probability": 0.34}

    negative_gradients = [y - 0.5 for y in ys]
    for y, expected in zip(ys, negative_gradients):
        close(-difference(lambda logit: binary_loss(logit, y), 0), expected)
    boost_rows = []
    initial_loss = mean([binary_loss(0, y) for y in ys])
    for eta in (1, 0.1):
        logits = [eta * gradient for gradient in negative_gradients]
        loss = mean([binary_loss(logit, y) for logit, y in zip(logits, ys)])
        assert loss < initial_loss
        assert [int(logit > 0) for logit in logits] == ys
        boost_rows.append({"eta": eta, "loss": loss, "probabilities": [sigmoid(z) for z in logits]})
    for axis in (0, 1):
        for left in (True, False):
            close(mean([g for x, g in zip(xs, negative_gradients) if (x[axis] <= 0) == left]), 0)
    results["boost_negative_gradient"] = {"initial_loss": initial_loss, "steps": boost_rows, "stump_leaf_means": [0, 0]}

    queries = [(0.8 * x[0], 0.8 * x[1]) for x in xs]
    nearest = lambda q: ys[min(range(4), key=lambda i: sum((a - b)**2 for a, b in zip(xs[i], q)))]
    predictions = {"logistic": [0] * 4, "linear_svm": [0] * 4,
                   "knn": [nearest(q) for q in queries], "rbf_svm": [int(score(q) > 0) for q in queries],
                   "manual_tree": [tree(q) for q in queries], "manual_forest": [int(averaged(q) > 0.5) for q in queries],
                   "manual_boost": [int(0.5 * (2 * tree(q) - 1) > 0) for q in queries]}
    for name, predicted in predictions.items():
        errors = sum(a != b for a, b in zip(predicted, ys))
        assert errors == (2 if name in ("logistic", "linear_svm") else 0)
    results["shared_query_predictions"] = {"queries": queries, "labels": ys, "predictions": predictions}

    # 11：链式缩放、稳定步长与解析二次函数的长程更新。
    chain = [{"layers": depth, "half": 0.5**depth, "one_and_half": 1.5**depth} for depth in (5, 10, 20)]
    for row in chain:
        depth = row["layers"]
        close(difference(lambda x: (0.5**depth) * x, 1), row["half"])
        close(difference(lambda x: (1.5**depth) * x, 1), row["one_and_half"], tolerance=1e-7)
    results["gradient_chain_initialization"] = {"chain": chain, "xavier_std": math.sqrt(2 / 200), "he_std": math.sqrt(2 / 100)}

    quadratic = lambda a, b: 0.5 * (a*a + 100*b*b)
    close(difference(lambda a: quadratic(a, 1), 1), 1, tolerance=1e-7)
    close(difference(lambda b: quadratic(1, b), 1), 100, tolerance=1e-7)
    learning_rows = []
    for eta in (0.1, 0.01):
        a, b = 1 - eta, 1 - 100 * eta
        learning_rows.append({"eta": eta, "parameters_after_one_step": [a, b], "loss": quadratic(a, b)})
    assert learning_rows[0]["loss"] > quadratic(1, 1) > learning_rows[1]["loss"]
    for eta in (0.005, 0.01, 0.019):
        assert quadratic((1 - eta)**100, (1 - 100 * eta)**100) < quadratic(1, 1)
    close(abs((1 - 100 * 0.02)**20), 1)
    assert abs((1 - 100 * 0.021)**20) > 1
    results["quadratic_learning_rate"] = {"initial_loss": 50.5, "steps": learning_rows, "stable_eta_interval": [0, 0.02]}

    gradients = [2, -1]
    sgd, momentum, velocity = 1, 1, 0
    sgd_rows = []
    for gradient in gradients:
        sgd -= 0.1 * gradient
        velocity = 0.9 * velocity + gradient
        momentum -= 0.1 * velocity
        sgd_rows.append({"sgd": sgd, "momentum": momentum, "velocity": velocity})
    close(sgd, 0.9)
    close(momentum, 0.72)
    results["sgd_momentum"] = sgd_rows

    theta, m, v = 1, 0, 0
    adam_rows = []
    for step, gradient in enumerate(gradients, 1):
        m = 0.9 * m + 0.1 * gradient
        v = 0.999 * v + 0.001 * gradient**2
        corrected_m, corrected_v = m / (1 - 0.9**step), v / (1 - 0.999**step)
        # 独立展开历史梯度权重，核对递推矩状态与偏差修正。
        weights_m = [0.9**(step - 1 - j) for j in range(step)]
        weights_v = [0.999**(step - 1 - j) for j in range(step)]
        close(corrected_m, sum(w*g for w, g in zip(weights_m, gradients[:step])) / sum(weights_m))
        close(corrected_v, sum(w*g*g for w, g in zip(weights_v, gradients[:step])) / sum(weights_v))
        theta -= 0.1 * corrected_m / (math.sqrt(corrected_v) + 1e-8)
        adam_rows.append({"step": step, "m": m, "v": v, "corrected_m": corrected_m, "corrected_v": corrected_v, "theta": theta})
    close(theta, 0.8733662967024315)
    results["adam_bias_correction"] = adam_rows

    theta, data_gradient, eta, decay = 1, 0.1, 0.1, 0.1
    combined_gradient = data_gradient + decay * theta
    sgd_decay = theta - eta * combined_gradient
    close(sgd_decay, (1 - eta * decay) * theta - eta * data_gradient)
    adam_coupled = theta - eta * combined_gradient / (abs(combined_gradient) + 1e-8)
    adamw = (1 - eta * decay) * theta - eta * data_gradient / (abs(data_gradient) + 1e-8)
    close(sgd_decay, 0.98)
    close(adam_coupled, 0.9, tolerance=1e-7)
    close(adamw, 0.89, tolerance=1e-7)
    results["weight_decay_algorithms"] = {"sgd_l2": sgd_decay, "adam_coupled_l2": adam_coupled, "adamw": adamw}

    gradient, limit = [3, 4], 1
    norm = math.sqrt(sum(g*g for g in gradient))
    clipped = [g * min(1, limit / norm) for g in gradient]
    close(math.sqrt(sum(g*g for g in clipped)), limit)
    close(clipped[0] / clipped[1], gradient[0] / gradient[1])
    small_gradient = [0.3, 0.4]
    close(min(1, limit / math.sqrt(sum(g*g for g in small_gradient))), 1)
    results["gradient_clipping"] = {"original": gradient, "clipped": clipped, "norm_limit": limit}

    batch = [1, 3]
    batch_mean = mean(batch)
    batch_variance = mean([(x - batch_mean)**2 for x in batch])
    training_outputs = [(x - batch_mean) / math.sqrt(batch_variance) for x in batch]
    evaluation_outputs = [x / 2 for x in batch]
    close(mean(training_outputs), 0)
    close(mean([x*x for x in training_outputs]), 1)
    unbiased_variance = sum((x - batch_mean)**2 for x in batch) / (len(batch) - 1)
    close(unbiased_variance, 2)
    ln_outputs = []
    for sample in ([1, 3], [11, 13]):
        mu = mean(sample)
        std = math.sqrt(mean([(x - mu)**2 for x in sample]))
        output = [(x - mu) / std for x in sample]
        assert output == [-1, 1]
        ln_outputs.append(output)
    results["normalization_modes"] = {"batch_mean": batch_mean, "batch_variance": batch_variance,
                                      "unbiased_variance": unbiased_variance, "bn_train": training_outputs,
                                      "bn_eval": evaluation_outputs, "ln_per_sample": ln_outputs, "epsilon_for_toy": 0}

    dropout_outputs = [[2 * a / 0.5, 4 * b / 0.5] for a, b in itertools.product((0, 1), repeat=2)]
    expectations = [mean([row[j] for row in dropout_outputs]) for j in range(2)]
    assert expectations == [2, 4]
    expected_loss = mean([0.5 * x**2 for x in (0, 4)])
    close(expected_loss, 4)
    assert expected_loss != 0.5 * 2**2
    results["dropout_expectation"] = {"outputs": dropout_outputs, "mean_activations": expectations,
                                      "scalar_expected_train_loss": expected_loss, "scalar_eval_loss": 2}

    print(json.dumps({"date": "2026-10-11", "python": platform.python_version(),
                      "scope": "09-11 artificial examples and analytic solutions; no real model training",
                      "checks_passed": len(results), "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
