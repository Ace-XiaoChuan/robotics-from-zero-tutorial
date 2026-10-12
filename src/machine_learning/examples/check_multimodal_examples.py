"""核对 12～17 的人工例子；不训练视觉、语言或扩散模型。"""

import itertools
import json
import math
import platform


def close(actual, expected, tolerance=1e-9):
    if not math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance):
        raise AssertionError(f"{actual} != {expected}")


def vector_close(actual, expected):
    assert len(actual) == len(expected)
    for first, second in zip(actual, expected):
        close(first, second)


def mean(values):
    return sum(values) / len(values)


def softmax(values):
    if not values or not any(math.isfinite(value) for value in values):
        raise ValueError("softmax 必须至少有一个有效位置")
    exponentials = [math.exp(value - max(values)) for value in values]
    total = sum(exponentials)
    return [value / total for value in exponentials]


def matmul(left, right):
    assert left and right and len(left[0]) == len(right)
    assert all(len(row) == len(left[0]) for row in left)
    assert all(len(row) == len(right[0]) for row in right)
    return [[sum(a * b for a, b in zip(row, column)) for column in zip(*right)] for row in left]


def attention(queries, keys, values, allowed=None):
    assert len(keys) == len(values) and len(queries[0]) == len(keys[0])
    weights, outputs = [], []
    for i, query in enumerate(queries):
        scores = [sum(q * k for q, k in zip(query, key)) / math.sqrt(len(query)) for key in keys]
        if allowed is not None:
            scores = [score if allowed[i][j] else -math.inf for j, score in enumerate(scores)]
        row = softmax(scores)
        weights.append(row)
        outputs.append([sum(p * value[j] for p, value in zip(row, values)) for j in range(len(values[0]))])
    return weights, outputs


def box_area(box):
    if len(box) != 4 or any(not math.isfinite(x) for x in box) or box[2] <= box[0] or box[3] <= box[1]:
        raise ValueError("仅接受连续坐标、有限数值的正面积框")
    return (box[2] - box[0]) * (box[3] - box[1])


def iou(first, second):
    areas = box_area(first) + box_area(second)
    width = max(0, min(first[2], second[2]) - max(first[0], second[0]))
    height = max(0, min(first[3], second[3]) - max(first[1], second[1]))
    overlap = width * height
    return overlap / (areas - overlap)


def nms(boxes, scores, threshold):
    candidates = sorted(range(len(boxes)), key=lambda i: scores[i], reverse=True)
    kept = []
    while candidates:
        current = candidates.pop(0)
        kept.append(current)
        candidates = [i for i in candidates if iou(boxes[current], boxes[i]) <= threshold]
    return kept


def recurrence(inputs, weight=0.5):
    state, outputs = 0, []
    for value in inputs:
        state = weight * state + value
        outputs.append(state)
    return outputs


def difference(function, value, step=1e-6):
    return (function(value + step) - function(value - step)) / (2 * step)


def contrastive_loss(similarities, temperature):
    return -math.log(softmax([s / temperature for s in similarities])[0])


def main():
    results = {}

    # 12：区域、匹配、排名与预处理坐标，全部是人工框/掩码。
    ground, shifted, blue = [120, 140, 220, 300], [140, 140, 240, 300], [380, 140, 480, 300]
    overlap = iou(ground, shifted)
    close(overlap, 2 / 3)
    close(iou(ground, ground), 1)
    close(iou(ground, blue), 0)
    close(iou([x * 0.35 for x in ground], [x * 0.35 for x in shifted]), overlap)
    for invalid in ([0, 0, 0, 1], [0, 0, -1, 1], [0, 0, math.nan, 1]):
        try:
            iou(ground, invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("非法框未拒绝")
    results["12_box_iou"] = {"ground_area_px2": box_area(ground), "iou": overlap,
                             "match_at_0_5": overlap >= 0.5, "match_at_0_75": overlap >= 0.75}

    boxes, scores = [ground, shifted, blue], [0.9, 0.8, 0.7]
    kept = nms(boxes, scores, 0.5)
    assert kept == [0, 2]
    assert nms(boxes, scores, 0.75) == [0, 1, 2]
    results["12_nms"] = {"kept_at_0_5": kept, "kept_at_0_75": [0, 1, 2]}

    truths, matched, tp_sequence, pr_rows = [ground, blue], set(), [], []
    for rank, prediction in enumerate(boxes, 1):
        available = [j for j in range(len(truths)) if j not in matched and iou(prediction, truths[j]) >= 0.5]
        tp = bool(available)
        if tp:
            selected = max(available, key=lambda j: iou(prediction, truths[j]))
            matched.add(selected)
        tp_sequence.append(tp)
        total_tp = sum(tp_sequence)
        pr_rows.append({"precision": total_tp / rank, "recall": total_tp / len(truths)})
    assert tp_sequence == [True, False, True]
    ap = sum(row["precision"] / len(truths) for tp, row in zip(tp_sequence, pr_rows) if tp)
    close(ap, 5 / 6)
    results["12_detection_ranking"] = {"tp_sequence": tp_sequence, "precision_recall": pr_rows,
                                      "noninterpolated_ap_not_coco": ap}

    truth_mask, prediction_mask = [1, 1, 0, 0, 1, 0], [1, 0, 0, 0, 1, 1]
    intersection = sum(a and b for a, b in zip(truth_mask, prediction_mask))
    union = sum(a or b for a, b in zip(truth_mask, prediction_mask))
    dice = 2 * intersection / (sum(truth_mask) + sum(prediction_mask))
    close(intersection / union, 0.5)
    close(dice, 2 / 3)
    results["12_mask_metrics"] = {"intersection": intersection, "union": union, "iou": 0.5, "dice": dice}

    keypoint_error = math.hypot(173 - 170, 224 - 220)
    close(keypoint_error, 5)
    assert keypoint_error <= 100 * 0.1 and keypoint_error > 20 * 0.1
    results["12_keypoints"] = {"error_px": keypoint_error, "pck_reference_100": True, "pck_reference_20": False}

    transformed = [x * 0.35 + (28 if j % 2 else 0) for j, x in enumerate(ground)]
    vector_close(transformed, [42, 77, 77, 133])
    restored = [(x - (28 if j % 2 else 0)) / 0.35 for j, x in enumerate(transformed)]
    vector_close(restored, ground)
    close(28 / 0.35, 80)
    results["12_letterbox_coordinates"] = {"processed_box": transformed, "restored_box": restored, "missed_padding_error_px": 80}

    # 13：历史信息、共享递推、门与教师强制。
    history_rows = []
    for positions, expected in (([0, 0.1, 0.2], 0.3), ([0.4, 0.3, 0.2], 0.1)):
        velocity = (positions[-1] - positions[-2]) / 0.1
        predicted = positions[-1] + velocity * 0.1
        close(predicted, expected)
        history_rows.append({"velocity_m_s": velocity, "next_position_m": predicted})
    assert history_rows[0]["velocity_m_s"] > 0 > history_rows[1]["velocity_m_s"]
    results["13_motion_history"] = history_rows

    states = recurrence([0, 1, 2])
    reverse_states = recurrence([2, 1, 0])
    vector_close(states, [0, 1, 2.5])
    vector_close(reverse_states, [2, 2, 1])
    results["13_rnn_states"] = {"states": states, "reversed_states": reverse_states}

    gradient_rows = []
    for inputs in ([0, 1, 2], [1, 1, 2]):
        loss = lambda a: 0.5 * (recurrence(inputs, a)[-1] - 3)**2
        final_state = recurrence(inputs)[-1]
        gradient = (final_state - 3) * (2 * 0.5 * inputs[0] + inputs[1])
        close(difference(loss, 0.5), gradient)
        gradient_rows.append({"inputs": inputs, "loss": loss(0.5), "shared_parameter_gradient": gradient})
    close(gradient_rows[0]["shared_parameter_gradient"], -0.5)
    results["13_bptt_gradient"] = gradient_rows

    gate_rows = []
    for gate in (0, 0.1, 0.9, 1):
        output = gate * 0.8 + (1 - gate) * 0.2
        assert 0.2 <= output <= 0.8
        gate_rows.append({"retain_gate": gate, "state": output})
    close(gate_rows[1]["state"], 0.26)
    close(gate_rows[2]["state"], 0.74)
    results["13_gru_retention"] = gate_rows

    probabilities = [0.8, 0.6, 0.5, 0.9]
    nll = mean([-math.log(p) for p in probabilities])
    close(nll, -math.log(math.prod(probabilities)) / 4)
    input_tokens, targets = ["开始", "猫", "在", "睡觉"], ["猫", "在", "睡觉", "结束"]
    assert input_tokens[1:] == targets[:-1]
    padded_probabilities = probabilities + [1e-12, 1e-12]
    valid_positions = [True] * 4 + [False] * 2
    padded_loss = sum(-math.log(p) for p, valid in zip(padded_probabilities, valid_positions) if valid) / sum(valid_positions)
    close(padded_loss, nll)  # 两个低概率 padding 不应改变有效 token 平均。
    results["13_teacher_forcing"] = {"sequence_probability": math.prod(probabilities), "mean_nll": nll, "valid_target_count": 4}

    # 14：投影、遮罩、置换性质、多头与单层缓存。
    x = [[1, 0], [0, 1], [1, 1]]
    identity, value_projection = [[1, 0], [0, 1]], [[1, 0], [0, 2]]
    q, k, v = matmul(x, identity), matmul(x, identity), matmul(x, value_projection)
    weights, output = attention(q, k, v)
    for row in weights:
        close(sum(row), 1)
    direct_exp = [1, math.exp(1 / math.sqrt(2)), math.exp(1 / math.sqrt(2))]
    vector_close(weights[1], [e / sum(direct_exp) for e in direct_exp])
    results["14_self_attention"] = {"Q": q, "K": k, "V": v, "second_weights": weights[1], "second_output": output[1]}

    allowed = [[j <= i for j in range(3)] for i in range(3)]
    causal_weights, causal_output = attention(q, k, v, allowed)
    perturbed = [x[0], x[1], [100, -100]]
    _, changed_output = attention(perturbed, perturbed, matmul(perturbed, value_projection), allowed)
    for first, second in zip(causal_output[:2], changed_output[:2]):
        vector_close(first, second)
    close(causal_weights[1][2], 0)
    try:
        attention([[1]], [[1]], [[1]], [[False]])
    except ValueError:
        pass
    else:
        raise AssertionError("全部屏蔽未拒绝")
    results["14_causal_mask"] = {"second_weights": causal_weights[1], "second_output": causal_output[1], "future_perturbation_first_two_unchanged": True}

    cross_weights, cross_output = attention([[1, 0]], [[1, 0], [0, 1]], [[10, 0], [0, 20]])
    _, permuted_cross = attention([[1, 0]], [[0, 1], [1, 0]], [[0, 20], [10, 0]])
    vector_close(cross_output[0], permuted_cross[0])
    results["14_cross_attention"] = {"weights_shape": [1, 2], "weights": cross_weights[0], "output": cross_output[0]}

    permutation = [2, 0, 1]
    _, permuted_output = attention([q[i] for i in permutation], [k[i] for i in permutation], [v[i] for i in permutation])
    for i, row in enumerate(permuted_output):
        vector_close(row, output[permutation[i]])
    positions = [[math.sin(i), math.cos(i)] for i in (0, 1)]
    assert positions[0] != positions[1]
    results["14_positions_permutation"] = {"position_vectors_d2": positions, "content_only_permutation_equivariance": True}

    heads = []
    for feature in (0, 1):
        selected = [[row[feature]] for row in x]
        _, head = attention(selected, selected, selected)
        heads.append(head)
    multi_output = [[heads[0][i][0], heads[1][i][0]] for i in range(3)]
    close(multi_output[1][0], 2 / 3)
    close(multi_output[1][1], 2 * math.e / (1 + 2 * math.e))
    results["14_multihead"] = {"two_heads_second_output": multi_output[1], "output_shape": [3, 2]}

    head_matrix = [[2, 1, 0], [0, 0, 0]]
    logits = matmul([[1, 0]], head_matrix)[0]
    probabilities = softmax(logits)
    vector_close(logits, [2, 1, 0])
    assert probabilities.index(max(probabilities)) == 0
    vector_close(probabilities, softmax([value + 100 for value in logits]))
    results["14_language_output"] = {"logits": logits, "probabilities": probabilities, "greedy_token": "猫"}

    cached_k, cached_v, cached_outputs = [], [], []
    for i in range(3):
        cached_k.append(k[i])
        cached_v.append(v[i])
        _, step_output = attention([q[i]], cached_k, cached_v)
        cached_outputs.append(step_output[0])
        vector_close(step_output[0], causal_output[i])
    results["14_kv_cache"] = {"single_layer_cached_outputs": cached_outputs, "illustrative_cache_bytes": 2 * 4 * 1 * 2 * 100 * 8 * 2,
                              "score_matrix_size_ratio_128_to_256": 4}

    # 15：重建、匹配、坍塌、增强与掩码目标。
    reconstruction_rows = []
    for sample in ([2, 0], [0, 2]):
        latent = mean(sample)
        reconstructed = [latent, latent]
        loss = 0.5 * sum((a - b)**2 for a, b in zip(sample, reconstructed))
        close(latent, 1)
        close(loss, 1)
        reconstruction_rows.append({"input": sample, "latent": latent, "reconstruction": reconstructed, "loss": loss})
    results["15_autoencoder_bottleneck"] = reconstruction_rows

    similarities, temperature = [0.8, 0], 0.2
    probabilities = softmax([s / temperature for s in similarities])
    loss = contrastive_loss(similarities, temperature)
    close(loss, math.log1p(math.exp(-4)))
    close(difference(lambda positive: contrastive_loss([positive, 0], temperature), 0.8), (probabilities[0] - 1) / temperature)
    results["15_contrastive_loss"] = {"positive_probability": probabilities[0], "loss": loss}

    collapsed_loss = contrastive_loss([1, 1], temperature)
    close(collapsed_loss, math.log(2))
    assert collapsed_loss > loss
    positive_only_zero_loss = sum((a - b)**2 for a, b in zip([0, 0], [0, 0]))
    close(positive_only_zero_loss, 0)
    results["15_representation_collapse"] = {"contrastive_collapsed_loss": collapsed_loss, "positive_only_zero_loss": positive_only_zero_loss}

    flip = lambda box: [640 - box[2], box[1], 640 - box[0], box[3]]
    flipped = flip(ground)
    vector_close(flipped, [420, 140, 520, 300])
    vector_close(flip(flipped), ground)
    close(box_area(flipped), box_area(ground))
    results["15_augmentation_coordinates"] = {"flipped_box": flipped, "double_flip_restores_original": True}

    target, prediction, hidden = [1, 2, 3, 4], [999, 2.5, -999, 3.5], [False, True, False, True]
    masked_mse = mean([(a - b)**2 for a, b, mask in zip(target, prediction, hidden) if mask])
    close(masked_mse, 0.25)
    patches = (224 // 16)**2
    assert patches == 196 and patches * 0.25 == 49 and patches * 0.75 == 147
    results["15_masked_prediction"] = {"masked_mse": masked_mse, "visible_patches": 49, "hidden_patches": 147}

    # 16：新补充机制；保留旧 VLM 检查器单独运行。
    candidate_rows = []
    for name, logits in (("original", [10, 9.6, -10]), ("remove_blue", [10, -10]), ("duplicate_red", [10, 10, 9.6, -10])):
        distribution = softmax(logits)
        candidate_rows.append({"configuration": name, "first_red_probability": distribution[0]})
    assert candidate_rows[1]["first_red_probability"] > candidate_rows[0]["first_red_probability"] > candidate_rows[2]["first_red_probability"]
    results["16_candidate_changes"] = candidate_rows

    visual = [[1, 0], [0, 1], [1, 1], [0, 0]]
    _, compressed = attention([[1, 0], [0, 1]], visual, visual)
    vector_close(compressed[0], [cross_weights[0][0], 0.5])
    vector_close(compressed[1], [0.5, cross_weights[0][0]])
    assert (448 // 16)**2 == 4 * (224 // 16)**2
    results["16_query_resampling"] = {"query_outputs": compressed, "visual_token_count_224_448": [196, 784], "visual_only_score_size_ratio": 16}

    connector_loss = lambda weight: 0.5 * (3 * (weight * 2) + 1 - 7)**2
    gradient = (4 - 7) * 3 * 2
    close(difference(connector_loss, 0.5), gradient)
    updated = 0.5 - 0.01 * gradient
    close(updated, 0.68)
    close(connector_loss(updated), 1.8432)
    assert connector_loss(updated) < connector_loss(0.5)
    results["16_frozen_module_gradient"] = {"connector_gradient": gradient, "updated_weight": updated, "loss_before": 4.5, "loss_after": connector_loss(updated)}

    truth_answers = ["红", "蓝", "蓝", "红"]
    evaluation_rows = []
    for answers in (["红"] * 4, truth_answers):
        correct = [a == b for a, b in zip(answers, truth_answers)]
        pairs = [correct[0] and correct[2], correct[1] and correct[3]]
        evaluation_rows.append({"answer_accuracy": mean(correct), "pair_accuracy": mean(pairs)})
    close(evaluation_rows[0]["answer_accuracy"], 0.5)
    close(evaluation_rows[0]["pair_accuracy"], 0)
    close(iou(ground, blue), 0)
    results["16_counterfactual_grounding"] = {"artificial_answer_schemes": evaluation_rows, "wrong_target_iou": iou(ground, blue)}

    # 17：条件均值、轨迹模式、扩散矩与采样代数；没有学出的去噪器。
    mse = lambda prediction: mean([(target - prediction)**2 for target in (-1, 1)])
    close(mse(0), 1)
    close(mse(1), 2)
    close(difference(mse, 0), 0)
    for value in (-2, -0.5, 0, 0.5, 2):
        close(mse(value), 1 + value**2)
    results["17_conditional_mean"] = {"mean": 0, "mse_mean": mse(0), "mse_at_mode": mse(1)}

    trajectory_samples = []
    for theta in (math.pi, 3 * math.pi / 4, math.pi / 2, math.pi / 4, 0):
        upper, lower = [math.cos(theta), math.sin(theta)], [math.cos(theta), -math.sin(theta)]
        average = [(a + b) / 2 for a, b in zip(upper, lower)]
        close(math.hypot(*upper), 1)
        close(math.hypot(*lower), 1)
        trajectory_samples.append({"upper_m": upper, "lower_m": lower, "average_m": average})
    assert math.hypot(*trajectory_samples[2]["average_m"]) < 0.25
    results["17_trajectory_modes"] = {"samples": trajectory_samples, "obstacle_radius_m": 0.25, "average_midpoint_collides": True}

    alpha, beta, cumulative_alpha, clean, epsilon = 0.8, 0.2, 0.64, 2, -1
    noisy = math.sqrt(cumulative_alpha) * clean + math.sqrt(1 - cumulative_alpha) * epsilon
    close(noisy, 1)
    # 独立零均值单位方差变量的四点枚举，核对 Markov 链一、二阶矩；不把 ±1 当作高斯分布。
    markov_values = []
    for first_noise, second_noise in itertools.product((-1, 1), repeat=2):
        first_state = math.sqrt(alpha) * clean + math.sqrt(beta) * first_noise
        second_state = math.sqrt(alpha) * first_state + math.sqrt(beta) * second_noise
        markov_values.append(second_state)
    close(mean(markov_values), 1.6)
    variance = mean([(value - mean(markov_values))**2 for value in markov_values])
    close(variance, 1 - cumulative_alpha)
    results["17_forward_noise"] = {"noisy_scalar": noisy, "conditional_mean": 1.6, "conditional_variance": variance}

    restore = lambda prediction: (noisy - math.sqrt(1 - cumulative_alpha) * prediction) / math.sqrt(cumulative_alpha)
    close(restore(epsilon), clean)
    estimate = restore(-0.8)
    close(estimate, 1.85)
    close(estimate - clean, -math.sqrt((1 - cumulative_alpha) / cumulative_alpha) * (-0.8 - epsilon))
    close(difference(restore, -0.8), -0.75)
    results["17_denoising_error"] = {"oracle_restored": restore(epsilon), "imperfect_restored": estimate, "noise_mse": (-0.8 - epsilon)**2, "amplification": 0.75}

    reverse_mean = (noisy - beta / math.sqrt(1 - cumulative_alpha) * epsilon) / math.sqrt(alpha)
    posterior_mean = math.sqrt(alpha) * beta / (1 - cumulative_alpha) * clean + math.sqrt(alpha) * (1 - alpha) / (1 - cumulative_alpha) * noisy
    close(reverse_mean, posterior_mean)
    posterior_variance = beta * (1 - alpha) / (1 - cumulative_alpha)
    close(posterior_variance, 1 / 9)
    ddim_first = math.sqrt(alpha) * restore(epsilon) + math.sqrt(1 - alpha) * epsilon
    ddim_final = (ddim_first - math.sqrt(1 - alpha) * epsilon) / math.sqrt(alpha)
    close(ddim_final, clean)
    results["17_sampling_algebra"] = {"oracle_ddpm_mean": reverse_mean, "posterior_variance": posterior_variance,
                                      "oracle_ddim_first": ddim_first, "oracle_ddim_final": ddim_final}

    unconditional, conditional = 0.2, -0.4
    guided = lambda scale: unconditional + scale * (conditional - unconditional)
    close(guided(0), unconditional)
    close(guided(1), conditional)
    close(guided(2), -1)
    results["17_condition_guidance"] = {"scale_2_prediction": guided(2), "scale_0_1_endpoints": [guided(0), guided(1)]}

    print(json.dumps({"date": "2026-10-11", "python": platform.python_version(), "checks_passed": len(results),
                      "scope": "12-17 artificial arrays, analytic gradients, regions and oracle sampling; no real models",
                      "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
