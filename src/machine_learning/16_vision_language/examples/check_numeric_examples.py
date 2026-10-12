"""核对 VLM 预习中的教学数值；只使用标准库，不加载或训练模型。"""

import json
import math


def dot(left, right):
    if len(left) != len(right):
        raise ValueError("点积要求向量维度一致")
    return sum(x * y for x, y in zip(left, right))


def softmax(logits):
    """减去最大值，避免大正数取指数溢出；要求非空、有限输入。"""
    maximum = max(logits)
    exps = [math.exp(value - maximum) for value in logits]
    total = sum(exps)
    return [value / total for value in exps]


def cosine(left, right):
    denominator = math.sqrt(dot(left, left) * dot(right, right))
    if denominator == 0:
        raise ValueError("零向量的余弦相似度未定义")
    return dot(left, right) / denominator


def cross_entropy(logits, target):
    """通过 log-sum-exp 计算单个正确候选的负对数概率。"""
    maximum = max(logits)
    return maximum + math.log(
        sum(math.exp(value - maximum) for value in logits)
    ) - logits[target]


def contrastive_loss(similarities, temperature):
    """一对一、同索引配对的方阵；行/列分别做交叉熵后平均。"""
    size = len(similarities)
    if size == 0 or any(len(row) != size for row in similarities):
        raise ValueError("需要非空方阵")
    if temperature <= 0:
        raise ValueError("温度必须为正")
    logits = [[score / temperature for score in row] for row in similarities]
    image_to_text = sum(cross_entropy(row, i) for i, row in enumerate(logits)) / size
    columns = list(zip(*logits))
    text_to_image = sum(cross_entropy(column, j) for j, column in enumerate(columns)) / size
    return (image_to_text + text_to_image) / 2


def attention(query, keys, values):
    """单 query 的缩放点积注意力；允许 key 与 value 维度不同。"""
    if not query or len(keys) != len(values) or not keys:
        raise ValueError("需要非空 query 和同数量的 key/value")
    width = len(values[0])
    if any(len(value) != width for value in values):
        raise ValueError("value 维度必须一致")
    scores = [dot(query, key) / math.sqrt(len(query)) for key in keys]
    weights = softmax(scores)
    output = [sum(w * value[j] for w, value in zip(weights, values)) for j in range(width)]
    return weights, output


def close(actual, expected):
    if not math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12):
        raise AssertionError(f"{actual} != {expected}")


def main():
    # 1：softmax 归一化、共同平移不变，以及文中概率。
    probabilities = softmax([2, 1, 0, -1])
    close(sum(probabilities), 1.0)
    close(probabilities[0], 0.6439142598879724)
    for actual, expected in zip(softmax([1002, 1001, 1000, 999]), probabilities):
        close(actual, expected)

    # 2：余弦结果及正比例缩放不变；候选分布。
    candidates = [[3, 4], [4, 3], [-3, -4]]
    similarities = [cosine([3, 4], candidate) for candidate in candidates]
    for actual, expected in zip(similarities, [1, 0.96, -1]):
        close(actual, expected)
    close(cosine([30, 40], candidates[1]), 0.96)
    matching = softmax([score / 0.1 for score in similarities])

    # 3：正确配对优于无区分与反配对；非对称矩阵检查行列交换不变。
    aligned = contrastive_loss([[1, 0], [0, 1]], 0.5)
    uniform = contrastive_loss([[0, 0], [0, 0]], 0.5)
    swapped = contrastive_loss([[0, 1], [1, 0]], 0.5)
    close(aligned, math.log1p(math.exp(-2)))
    close(uniform, math.log(2))
    close(swapped - aligned, 2)
    asymmetric = [[2, 1], [0, 3]]
    close(contrastive_loss(asymmetric, 0.5),
          contrastive_loss(list(zip(*asymmetric)), 0.5))

    # 4：从 token 输入和三组权重生成 Q/K/V，再计算“杯”位置的注意力。
    tokens = [[1, 0], [0.5, 0.5]]
    projection_weights = {
        "Q": [[1], [1]],
        "K": [[1], [-1]],
        "V": [[2, 0], [-2, 4]],
    }
    qkv = {
        name: [[dot(token, column) for column in zip(*matrix)] for token in tokens]
        for name, matrix in projection_weights.items()
    }
    expected_qkv = {"Q": [[1], [1]], "K": [[1], [0]], "V": [[2, 0], [0, 2]]}
    if qkv != expected_qkv:
        raise AssertionError(f"Q/K/V 投影结果不符：{qkv}")
    weights, attended = attention(qkv["Q"][1], qkv["K"], qkv["V"])
    close(weights[0], 1 / (1 + math.exp(-1)))
    close(attended[0], 2 * weights[0])
    close(attended[1], 2 * weights[1])
    _, reordered = attention([1], [[0], [1]], [[0, 2], [2, 0]])
    for actual, expected in zip(reordered, attended):
        close(actual, expected)

    # 5：连接器列向量约定，以及 patch 数。
    projected = [dot(row, [2, 1]) for row in [[1, 0], [0, 1], [1, 1]]]
    if projected != [2, 1, 3] or (224 // 16) ** 2 != 196:
        raise AssertionError("连接器或 patch 计数不符")

    # 6：仅两个回答 token 的平均负对数概率。
    answer_loss = -(math.log(0.8) + math.log(0.5)) / 2
    close(answer_loss, -math.log(math.sqrt(0.4)))

    # 7：单层 LoRA 参数与比例。
    base_parameters = 4096 * 4096
    lora_parameters = 8 * (4096 + 4096)
    close(lora_parameters / base_parameters, 0.00390625)

    # 8：框中心、米制反投影以及重新投影回像素。
    u, v = (120 + 220) / 2, (140 + 300) / 2
    z = 0.60
    x, y = (u - 320) * z / 600, (v - 240) * z / 600
    close(x, -0.15)
    close(y, -0.02)
    close(600 * x / z + 320, u)
    close(600 * y / z + 240, v)

    print(json.dumps({
        "checks_passed": 8,
        "next_token_probabilities": probabilities,
        "cosine_similarities": similarities,
        "candidate_probabilities": matching,
        "contrastive_loss": aligned,
        "uniform_contrastive_loss": uniform,
        "qkv_from_token_features": qkv,
        "attention_weights": weights,
        "attention_output": attended,
        "projected_feature": projected,
        "answer_loss": answer_loss,
        "lora_parameters": lora_parameters,
        "lora_fraction": lora_parameters / base_parameters,
        "pixel_center": [u, v],
        "camera_point_m": [x, y, z],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
