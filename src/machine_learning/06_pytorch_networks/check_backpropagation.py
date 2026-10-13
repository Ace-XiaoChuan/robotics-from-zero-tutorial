"""核对交叉熵与两层 MLP 的完整梯度；默认只使用 Python 标准库。

从仓库根目录运行：
    python3 src/machine_learning/06_pytorch_networks/check_backpropagation.py
可选 --torch：与现有 DigitMLP 的 PyTorch 自动求导比较，不读数据、不更新参数。
"""

import argparse
import copy
import importlib.util
import math
from pathlib import Path
import sys


GRADIENT_NAMES = ("W1", "b1", "W2", "b2", "X")


def example():
    """B=2、D=2、H=2、C=3；每行是一个样本或一个输出单元的权重。"""
    return {
        "X": [[1.0, 2.0], [-1.0, 1.0]],
        "W1": [[0.5, -0.25], [-0.5, 0.5]],
        "b1": [0.25, 0.25],
        "W2": [[1.0, 0.0], [0.0, 1.0], [-1.0, 0.5]],
        "b2": [0.0, 0.0, 0.0],
    }, [1, 2]


def affine(rows, weights, bias):
    """Y = X W^T + b；weights 的行数是输出维数。"""
    return [[sum(x * w for x, w in zip(row, output_weights)) + b
             for output_weights, b in zip(weights, bias)] for row in rows]


def cross_entropy(logits, labels, reduction="mean"):
    """直接从 logits 求稳定的交叉熵；不对下溢后的概率取 log。"""
    if reduction not in {"mean", "sum"}:
        raise ValueError("reduction 必须是 mean 或 sum。")
    probabilities, losses = [], []
    for row, label in zip(logits, labels):
        maximum = max(row)
        exponentials = [math.exp(value - maximum) for value in row]
        normalizer = sum(exponentials)
        probabilities.append([value / normalizer for value in exponentials])
        losses.append(maximum + math.log(normalizer) - row[label])
    divisor = len(labels) if reduction == "mean" else 1
    return sum(losses) / divisor, probabilities, losses


def forward(state, labels, reduction="mean"):
    a = affine(state["X"], state["W1"], state["b1"])
    h = [[max(0.0, value) for value in row] for row in a]
    z = affine(h, state["W2"], state["b2"])
    loss, p, losses = cross_entropy(z, labels, reduction)
    return {"A": a, "H": h, "Z": z, "P": p, "losses": losses, "loss": loss}


def backward(state, labels, trace, reduction="mean"):
    """按 backpropagation.md 的逐分量求和实现梯度，不使用自动微分。"""
    x, w1, w2 = state["X"], state["W1"], state["W2"]
    a, h, p = trace["A"], trace["H"], trace["P"]
    batch, inputs, hidden, classes = len(x), len(x[0]), len(w1), len(w2)
    divisor = batch if reduction == "mean" else 1
    # mean 的 1/B 只在损失入口乘一次，后续各层不再重复除以 B。
    dz = [[(p[i][c] - int(labels[i] == c)) / divisor
           for c in range(classes)] for i in range(batch)]
    dw2 = [[sum(dz[i][c] * h[i][k] for i in range(batch))
            for k in range(hidden)] for c in range(classes)]
    db2 = [sum(dz[i][c] for i in range(batch)) for c in range(classes)]
    dh = [[sum(dz[i][c] * w2[c][k] for c in range(classes))
           for k in range(hidden)] for i in range(batch)]
    # 在 A=0 处采用框架常用的 0 约定；数值差分例子避开不可导点。
    da = [[dh[i][k] if a[i][k] > 0.0 else 0.0
           for k in range(hidden)] for i in range(batch)]
    dw1 = [[sum(da[i][k] * x[i][d] for i in range(batch))
            for d in range(inputs)] for k in range(hidden)]
    db1 = [sum(da[i][k] for i in range(batch)) for k in range(hidden)]
    dx = [[sum(da[i][k] * w1[k][d] for k in range(hidden))
           for d in range(inputs)] for i in range(batch)]
    return {"W1": dw1, "b1": db1, "W2": dw2, "b2": db2, "X": dx,
            "DZ": dz, "DH": dh, "DA": da}


def scalar_items(value, path=()):
    if isinstance(value, list):
        for index, child in enumerate(value):
            yield from scalar_items(child, path + (index,))
    else:
        yield path, value


def replace_scalar(value, path, new_value):
    for index in path[:-1]:
        value = value[index]
    value[path[-1]] = new_value


def values(value):
    return [item for _, item in scalar_items(value)]


def shape(value):
    if not isinstance(value, list):
        return ()
    child_shape = shape(value[0])
    assert all(shape(child) == child_shape for child in value), "输入不是规则数组。"
    return (len(value),) + child_shape


def check_close(actual, expected, tolerance=1e-10):
    assert shape(actual) == shape(expected), "比较的数组形状不一致。"
    actual, expected = values(actual), values(expected)
    assert len(actual) == len(expected), "比较的元素数不一致。"
    assert all(math.isfinite(value) for value in actual + expected), "出现非有限值。"
    error = max(abs(a - b) for a, b in zip(actual, expected))
    assert error <= tolerance, f"最大绝对误差 {error:.3e} 超过 {tolerance:.3e}"
    return error


def check_finite_differences(state, labels):
    """逐次只扰动一个标量并重算前向 loss，独立核对两种 reduction。"""
    epsilon, errors, count = 1e-6, [], 0
    for reduction in ("mean", "sum"):
        expected = backward(state, labels, forward(state, labels, reduction), reduction)
        for name in GRADIENT_NAMES:
            for path, original in scalar_items(state[name]):
                plus, minus = copy.deepcopy(state), copy.deepcopy(state)
                replace_scalar(plus[name], path, original + epsilon)
                replace_scalar(minus[name], path, original - epsilon)
                numerical = (forward(plus, labels, reduction)["loss"]
                             - forward(minus, labels, reduction)["loss"]) / (2 * epsilon)
                analytic = expected[name]
                for index in path:
                    analytic = analytic[index]
                errors.append(check_close(numerical, analytic, 1e-8))
                count += 1
    return count, max(errors)


def check_batch_scale(state, labels):
    mean = backward(state, labels, forward(state, labels))
    summed = backward(state, labels, forward(state, labels, "sum"), "sum")
    batch = len(labels)
    for name in GRADIENT_NAMES:
        check_close(values(summed[name]), [batch * g for g in values(mean[name])])

    # 分别计算单样本梯度，共享参数的梯度应等于它们的平均。
    individual = []
    for i, label in enumerate(labels):
        one = copy.deepcopy(state)
        one["X"] = [state["X"][i][:]]
        individual.append(backward(one, [label], forward(one, [label])))
    for name in GRADIENT_NAMES[:-1]:
        per_sample = [values(gradient[name]) for gradient in individual]
        check_close(values(mean[name]),
                    [sum(column) / batch for column in zip(*per_sample)])
    for i, gradient in enumerate(individual):
        check_close(mean["X"][i], [g / batch for g in gradient["X"][0]])

    # 两份独立输入复制成四个样本：共享参数梯度不变，每行输入梯度减半。
    duplicated = copy.deepcopy(state)
    duplicated["X"] += copy.deepcopy(state["X"])
    repeated = backward(duplicated, labels + labels, forward(duplicated, labels + labels))
    for name in GRADIENT_NAMES[:-1]:
        check_close(repeated[name], mean[name])
    for i in range(2 * batch):
        check_close(repeated["X"][i], [g / 2 for g in mean["X"][i % batch]])


def check_cross_entropy(trace, labels, gradient):
    epsilon, errors = 1e-6, []
    for i, row in enumerate(trace["Z"]):
        for c, original in enumerate(row):
            plus, minus = copy.deepcopy(trace["Z"]), copy.deepcopy(trace["Z"])
            plus[i][c], minus[i][c] = original + epsilon, original - epsilon
            numerical = (cross_entropy(plus, labels)[0] - cross_entropy(minus, labels)[0]) / (2 * epsilon)
            errors.append(check_close(numerical, gradient["DZ"][i][c], 1e-8))
        check_close(sum(trace["P"][i]), 1.0)
        check_close(sum(gradient["DZ"][i]), 0.0)
    # 全部 logits 加同一常数不改变概率或损失，+1000 仍能稳定计算。
    shifted = [[value + 1000 for value in row] for row in trace["Z"]]
    shifted_loss, shifted_p, _ = cross_entropy(shifted, labels)
    check_close(shifted_loss, trace["loss"])
    check_close(shifted_p, trace["P"])
    return len(errors), max(errors)


def check_torch():
    """在现有默认 DigitMLP 上比较全部参数和输入梯度，不执行 optimizer.step。"""
    import torch

    sys.dont_write_bytecode = True
    path = Path(__file__).resolve().parent / "src" / "model.py"
    spec = importlib.util.spec_from_file_location("digit_mlp_gradient_check", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    torch.set_num_threads(1)
    torch.manual_seed(42)
    relu_probe = torch.tensor([-1.0, 0.0, 1.0], dtype=torch.float64, requires_grad=True)
    torch.nn.functional.relu(relu_probe).sum().backward()
    assert relu_probe.grad.tolist() == [0.0, 0.0, 1.0]
    model = module.DigitMLP().double()
    images = torch.linspace(0.05, 0.95, 2 * 28 * 28, dtype=torch.float64)
    images = images.reshape(2, 1, 28, 28).requires_grad_(True)
    labels = torch.tensor([2, 7], dtype=torch.long)
    before = {name: value.detach().clone() for name, value in model.state_dict().items()}
    first, second = model.layers[1], model.layers[3]
    assert tuple(first.weight.shape) == (128, 784)
    assert tuple(first.bias.shape) == (128,)
    assert tuple(second.weight.shape) == (10, 128)
    assert tuple(second.bias.shape) == (10,)
    logits = model(images)
    assert tuple(logits.shape) == (2, 10)
    loss = torch.nn.CrossEntropyLoss()(logits, labels)
    loss.backward()
    assert tuple(images.grad.shape) == (2, 1, 28, 28)

    state = {"X": images.detach().flatten(1).tolist(),
             "W1": first.weight.detach().tolist(), "b1": first.bias.detach().tolist(),
             "W2": second.weight.detach().tolist(), "b2": second.bias.detach().tolist()}
    trace = forward(state, labels.tolist())
    expected = backward(state, labels.tolist(), trace)
    errors = [check_close(logits.detach().tolist(), trace["Z"]),
              check_close(loss.item(), trace["loss"])]
    actual = {"W1": first.weight.grad.tolist(), "b1": first.bias.grad.tolist(),
              "W2": second.weight.grad.tolist(), "b2": second.bias.grad.tolist(),
              "X": images.grad.flatten(1).tolist()}
    for name in GRADIENT_NAMES:
        errors.append(check_close(actual[name], expected[name]))
    assert all(torch.equal(before[name], value) for name, value in model.state_dict().items())
    count = sum(len(values(actual[name])) for name in GRADIENT_NAMES)
    print(f"PyTorch {torch.__version__}：DigitMLP [2,784] → [2,128] → [2,10]，"
          f"{count} 个参数/输入梯度相符，最大误差 {max(errors):.3e}；参数未更新。")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--torch", action="store_true", help="额外核对现有 DigitMLP 的自动求导")
    arguments = parser.parse_args()
    state, labels = example()
    trace = forward(state, labels)
    gradient = backward(state, labels, trace)
    check_close(trace["A"], [[0.25, 0.75], [-0.5, 1.25]])
    check_close(trace["H"], [[0.25, 0.75], [0.0, 1.25]])
    check_close(trace["Z"], [[0.25, 0.75, 0.125], [0.0, 1.25, 0.625]])
    assert gradient["DA"][1][0] == 0.0 and gradient["DH"][1][0] != 0.0
    count, error = check_finite_differences(state, labels)
    logits_count, logits_error = check_cross_entropy(trace, labels, gradient)
    check_batch_scale(state, labels)
    print(f"小例子：两项交叉熵 {trace['losses'][0]:.9f}、{trace['losses'][1]:.9f}，"
          f"平均损失 {trace['loss']:.9f}。")
    print(f"参数与输入：mean/sum 共 {count} 个中央差分检查通过，最大误差 {error:.3e}。")
    print(f"logits：{logits_count} 个中央差分检查通过，最大误差 {logits_error:.3e}。")
    print("批量平均、单样本贡献、复制批次、ReLU mask 与平移稳定性检查通过。")
    if arguments.torch:
        check_torch()


if __name__ == "__main__":
    main()
