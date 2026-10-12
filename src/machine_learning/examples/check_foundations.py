"""核对 01～08 的教学数值；标准库实现，不训练模型或驱动机器人。"""

import json
import math


def close(actual, expected, *, tolerance=1e-9):
    if not math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance):
        raise AssertionError(f"{actual} != {expected}")


def squared_distance(left, right):
    if len(left) != len(right):
        raise ValueError("向量维度不一致")
    return sum((a - b) ** 2 for a, b in zip(left, right))


def mean(values):
    return sum(values) / len(values)


def softmax(values):
    exponentials = [math.exp(value - max(values)) for value in values]
    total = sum(exponentials)
    return [value / total for value in exponentials]


def network(parameters, inputs=(1.0, 2.0), target=2.0):
    w1, w2, bias, output_weight, output_bias = parameters
    activation = w1 * inputs[0] + w2 * inputs[1] + bias
    hidden = max(0.0, activation)
    prediction = output_weight * hidden + output_bias
    return prediction, 0.5 * (prediction - target) ** 2


def target_rejection(target, *, now_s, clock="ros", min_score=0.8, max_age_s=0.3):
    """教学候选筛选：base 下的物体点；不判断 IK、碰撞、姿态或执行能力。"""
    if target.get("clock") != clock:
        return "clock"
    if target.get("frame_id") != "base":
        return "frame"
    score = target.get("score")
    stamp = target.get("stamp_s")
    if not isinstance(score, (float, int)) or not math.isfinite(score) or not 0 <= score <= 1:
        return "score"
    if score < min_score:
        return "score"
    if target.get("class_id") != "cup":
        return "class"
    if not isinstance(stamp, (float, int)) or not math.isfinite(stamp) or not math.isfinite(now_s):
        return "time"
    age = now_s - stamp
    if age < -1e-9 or age > max_age_s + 1e-9:
        return "time"
    point = target.get("point_m")
    if not isinstance(point, (list, tuple)) or len(point) != 3:
        return "geometry"
    if any(not isinstance(value, (float, int)) or not math.isfinite(value) for value in point):
        return "geometry"
    # 仅是本例的粗略范围；不是机械臂真实工作空间或碰撞检查。
    bounds = ((0.2, 0.8), (-0.3, 0.3), (0.1, 1.0))
    if any(value < low or value > high for value, (low, high) in zip(point, bounds)):
        return "range"
    return None


def main():
    results = {}

    # 01：改变表示单位后原始距离反转；按同一物理尺度归一化则不变。
    query = (1.0, 100.0)
    points = ((1.1, 300.0), (2.0, 110.0))
    raw = [math.sqrt(squared_distance(point, query)) for point in points]
    kg = [math.sqrt(squared_distance((p[0], p[1] / 1000), (1, 0.1))) for p in points]
    assert raw[1] < raw[0] and kg[0] < kg[1]
    normalized = [((p[0] - query[0]), (p[1] - query[1]) / 100) for p in points]
    normalized_kg = [((p[0] - 1), (p[1] / 1000 - 0.1) / 0.1) for p in points]
    for first, second in zip(normalized, normalized_kg):
        close(squared_distance(first, (0, 0)), squared_distance(second, (0, 0)))
    results["knn_scale"] = {"raw_m_g": raw, "raw_m_kg": kg}

    neighbors = [(0.1, "B"), (0.2, "A"), (0.3, "A")]
    assert neighbors[0][1] == "B"
    assert sum(label == "A" for _, label in neighbors) == 2
    weighted_a = sum(1 / distance for distance, label in neighbors if label == "A")
    weighted_b = sum(1 / distance for distance, label in neighbors if label == "B")
    assert weighted_b > weighted_a
    for x in (-2, -0.1, 0, 0.1, 2):
        close(squared_distance((x, 0.7), (-1, 0)) - squared_distance((x, 0.7), (1, 0)), 4 * x)
    results["knn_votes_boundary"] = {"k1": "B", "k3": "A", "distance_weighted_k3": "B"}

    # 02：独立闭式解、梯度驻点和 L1/L2 目标比较。
    x, y = [0, 1, 2], [1, 2, 2]
    slope = sum((a - mean(x)) * (b - mean(y)) for a, b in zip(x, y)) / sum((a - mean(x)) ** 2 for a in x)
    intercept = mean(y) - slope * mean(x)
    residuals = [b - (intercept + slope * a) for a, b in zip(x, y)]
    close(slope, 0.5)
    close(intercept, 7 / 6)
    close(mean([r * r for r in residuals]), 1 / 18)
    close(sum(residuals), 0)
    close(sum(a * r for a, r in zip(x, residuals)), 0)
    updated_predictions = [1 / 3 + 0.4 * value for value in x]
    close(mean([(a - b) ** 2 for a, b in zip(updated_predictions, y)]), 14 / 15)
    results["least_squares"] = {"slope": slope, "intercept": intercept, "mse": 1 / 18, "first_step_mse": 14 / 15}

    regularization = []
    data_loss = lambda coefficient: (2 / 3) * (coefficient - 2) ** 2
    for strength in (0, 1, 3):
        ridge = (4 / 3) / (2 / 3 + strength)
        lasso = max(0, 2 - 3 * strength / 4)
        for optimum, penalty in ((ridge, lambda w: w * w), (lasso, abs)):
            objective = lambda w: data_loss(w) + strength * penalty(w)
            for delta in (-0.2, -0.01, 0.01, 0.2):
                assert objective(optimum) <= objective(optimum + delta) + 1e-12
        regularization.append({"lambda": strength, "l2": ridge, "l1": lasso})
    results["l1_l2"] = regularization

    # 03：标准化、类别表示、阈值与混淆矩阵的守恒关系。
    training = [20, 40]
    standard_deviation = math.sqrt(mean([(value - mean(training)) ** 2 for value in training]))
    close(standard_deviation, 10)
    close((80 - mean(training)) / standard_deviation, 5)
    encoding = {"红": [1, 0], "蓝": [0, 1], "黄": [0, 0]}
    assert encoding["红"] != encoding["蓝"] and sum(encoding["黄"]) == 0
    results["preprocessing"] = {"training_mean": 30, "training_std": 10, "validation_z": 5, "one_hot": encoding}

    labels, scores = [1, 1, 0, 1, 0, 0], [0.95, 0.70, 0.65, 0.40, 0.35, 0.10]
    rows = []
    for threshold, expected in ((0.3, (3, 2, 0, 1)), (0.5, (2, 1, 1, 2)), (0.8, (1, 0, 2, 3))):
        predicted = [score >= threshold for score in scores]
        tp = sum(p and label == 1 for p, label in zip(predicted, labels))
        fp = sum(p and label == 0 for p, label in zip(predicted, labels))
        fn = sum(not p and label == 1 for p, label in zip(predicted, labels))
        tn = sum(not p and label == 0 for p, label in zip(predicted, labels))
        assert (tp, fp, fn, tn) == expected and tp + fp + fn + tn == len(labels)
        rows.append({"threshold": threshold, "tp_fp_fn_tn": expected, "precision": tp / (tp + fp), "recall": tp / (tp + fn)})
    results["thresholds"] = rows

    # 04：固定 x 下对训练集变化取平均；直接枚举新标签噪声验证分解。
    decomposition = []
    for predictions in ([1, 2, 3], [1.5, 1.5, 1.5]):
        bias_squared = (mean(predictions) - 2) ** 2
        variance = mean([(p - mean(predictions)) ** 2 for p in predictions])
        error = mean([(p - (2 + noise)) ** 2 for p in predictions for noise in (-0.5, 0.5)])
        close(error, bias_squared + variance + 0.25)
        decomposition.append({"bias_squared": bias_squared, "variance": variance, "expected_mse": error})
    results["bias_variance"] = decomposition
    split = {"train": {"A", "B"}, "validation": {"C"}, "test": {"D"}}
    assert not (split["train"] & split["validation"] or split["train"] & split["test"] or split["validation"] & split["test"])
    results["group_split"] = {key: sorted(value) for key, value in split.items()}

    # 05：二维聚类更新；PCA 特征方程、正交分解和重建误差。
    points = [(0, 0), (0, 2), (8, 0), (8, 2)]
    initial = [(0, 0), (8, 0)]
    assignments = [min(range(2), key=lambda i: squared_distance(point, initial[i])) for point in points]
    centers = [tuple(mean([point[axis] for point, group in zip(points, assignments) if group == i]) for axis in range(2)) for i in range(2)]
    assert centers == [(0, 1), (8, 1)]
    close(sum(squared_distance(point, centers[group]) for point, group in zip(points, assignments)), 4)
    results["kmeans_2d"] = {"centers": centers, "sse": 4}

    centered = [(p[0] - 4, p[1] - 1) for p in points]
    covariance = [[sum(p[i] * p[j] for p in centered) / 3 for j in range(2)] for i in range(2)]
    close(covariance[0][0], 64 / 3)
    close(covariance[1][1], 4 / 3)
    close(covariance[0][1], 0)
    scores = [p[0] for p in centered]
    reconstructed = [(score + 4, 1) for score in scores]
    close(sum(squared_distance(p, restored) for p, restored in zip(points, reconstructed)), 4)
    close(covariance[0][0] / (covariance[0][0] + covariance[1][1]), 16 / 17)
    assert scores[0] == scores[1] and points[0][1] != points[1][1]
    results["pca"] = {"covariance": covariance, "scores": scores, "explained_ratio": 16 / 17, "reconstruction_sse": 4}

    # 06：反向梯度与中央差分逐参数交叉核对，远离 ReLU 不可导点。
    parameters = [0.5, -0.5, 1, 2, 0.5]
    gradients = [-1, -2, -1, -0.25, -0.5]
    prediction, loss = network(parameters)
    close(prediction, 1.5)
    close(loss, 0.125)
    for i, expected in enumerate(gradients):
        plus, minus = parameters.copy(), parameters.copy()
        plus[i] += 1e-6
        minus[i] -= 1e-6
        difference = (network(plus)[1] - network(minus)[1]) / 2e-6
        close(difference, expected, tolerance=1e-8)
    updated = [p - 0.05 * g for p, g in zip(parameters, gradients)]
    updated_prediction, updated_loss = network(updated)
    close(updated_prediction, 2.135)
    close(updated_loss, 0.0091125)
    assert updated_loss < loss
    larger_step = [p - 0.1 * g for p, g in zip(parameters, gradients)]
    close(network(larger_step)[1], 0.302253125)
    assert network(larger_step)[1] > loss
    results["backpropagation"] = {"gradients": gradients, "updated_parameters": updated, "updated_prediction": updated_prediction, "updated_loss": updated_loss, "larger_step_loss": network(larger_step)[1]}
    probabilities = softmax([2, 1, 0])
    logit_gradient = [p - int(i == 0) for i, p in enumerate(probabilities)]
    close(sum(logit_gradient), 0)
    for i, expected in enumerate(logit_gradient):
        plus, minus = [2.0, 1.0, 0.0], [2.0, 1.0, 0.0]
        plus[i] += 1e-6
        minus[i] -= 1e-6
        difference = (-math.log(softmax(plus)[0]) + math.log(softmax(minus)[0])) / 2e-6
        close(difference, expected, tolerance=1e-8)
    results["cross_entropy_gradient"] = logit_gradient

    # 07：互相关、池化与感受野/参数数目；不加载 ResNet 或权重。
    image, kernel = [[1, 2, 3], [4, 5, 6], [7, 8, 0]], [[1, 0], [0, -1]]
    convolution = [[sum(image[row + i][col + j] * kernel[i][j] for i in range(2) for j in range(2)) for col in range(2)] for row in range(2)]
    assert convolution == [[-4, -4], [-4, 5]]
    activated = [[max(0, value) for value in row] for row in convolution]
    close(mean([value for row in activated for value in row]), 1.25)
    results["convolution_pooling"] = {"feature_map": convolution, "relu_map": activated, "global_average": 1.25}
    receptive_field, jump = 1, 1
    for kernel_size, stride in ((3, 1), (3, 1)):
        receptive_field += (kernel_size - 1) * jump
        jump *= stride
    assert receptive_field == 5
    assert 2 * (3 * 3 * 3 + 1) == 56
    results["receptive_field_parameters"] = {"two_3x3_receptive_field": receptive_field, "rgb_to_two_channels_parameters": 56}

    # 08：点变换的往返与距离保持；条件筛选覆盖失效与边界输入。
    camera_point = ((380 - 320) * 0.5 / 400, (260 - 240) * 0.5 / 400, 0.5)
    base_point = (camera_point[2] + 0.2, -camera_point[0], 0.8 - camera_point[1])
    restored = (-base_point[1], 0.8 - base_point[2], base_point[0] - 0.2)
    for first, second in zip(camera_point, restored):
        close(first, second)
    close(squared_distance(camera_point, (0, 0, 0)), squared_distance(base_point, (0.2, 0, 0.8)))
    grasp_point = (base_point[0], base_point[1], base_point[2] + 0.1)
    results["robot_geometry"] = {"camera_point_m": camera_point, "base_point_m": base_point, "grasp_tcp_m": grasp_point}

    target = {"clock": "ros", "frame_id": "base", "class_id": "cup", "score": 0.94, "stamp_s": 10, "point_m": base_point}
    assert target_rejection(target, now_s=10.25) is None
    assert target_rejection(target, now_s=10.3) is None
    assert target_rejection({**target, "score": 0.8}, now_s=10.25) is None
    failure_cases = [("score", 0.6, "score"), ("score", math.nan, "score"), ("frame_id", "camera_optical", "frame"), ("clock", "system", "clock"), ("class_id", "bottle", "class"), ("point_m", None, "geometry"), ("point_m", (0.7, math.nan, 0.775), "geometry"), ("point_m", (700, -75, 775), "range"), ("stamp_s", 9.6, "time"), ("stamp_s", 11, "time")]
    for key, value, reason in failure_cases:
        assert target_rejection({**target, key: value}, now_s=10.25) == reason
    results["robot_candidate_conditions"] = {"valid_candidate": True, "rejections_checked": len(failure_cases), "age_s": 0.25}
    close(0.2 * 0.25, 0.05)
    close((38 / 40) * (34 / 38) * (32 / 34) * (26 / 32), 26 / 40)
    results["robot_latency_success"] = {"motion_during_age_m": 0.05, "task_success_ratio": 0.65}

    print(json.dumps({"checks_passed": len(results), "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
