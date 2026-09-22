"""准备预训练 ResNet18，并检查三分类前向传播；尚不执行训练。"""

import argparse
import json
from pathlib import Path

import torch
from torch import nn
from torchvision.models import ResNet18_Weights, resnet18

from data import CLASS_TO_IDX, make_dataloaders


PROJECT_DIR = Path(__file__).resolve().parents[1]
WEIGHTS = ResNet18_Weights.IMAGENET1K_V1
DEFAULT_CACHE_DIR = PROJECT_DIR / "outputs" / "pretrained"


def set_head_training_mode(model):
    """后续每轮只训练分类头时调用：冻结部分保持 eval(evaluation mode)，分类头设为 train。"""
    # requires_grad=False 只冻结参数；eval 还会阻止 BatchNorm 更新运行统计量。
    model.eval()
    model.fc.train()


def build_model(cache_dir=DEFAULT_CACHE_DIR):
    """加载完整预训练参数，冻结旧参数，再创建可训练的新分类头。"""
    # 先搭建原始 1000 类结构，再完整加载官方权重。
    # 显式指定项目内缓存，首次下载，之后复用；失败会报错，不回退到随机权重。
    model = resnet18(weights=None)
    state = torch.hub.load_state_dict_from_url(
        WEIGHTS.url, model_dir=str(cache_dir), check_hash=True,
        map_location="cpu", weights_only=True,
    )
    model.load_state_dict(state, strict=True)

    for parameter in model.parameters():
        parameter.requires_grad_(False)

    # 原 fc 是 Linear(512, 1000)。新层的权重和偏置随机初始化，默认需要梯度。
    # 输入特征数从模型读取，类别顺序与 data.py 中的映射保持一致。
    model.fc = nn.Linear(model.fc.in_features, len(CLASS_TO_IDX))
    set_head_training_mode(model)
    return model


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    torch.set_num_threads(2)
    torch.manual_seed(42)  # 固定新分类头的初始化，方便重复检查。
    model = build_model()
    images, labels = next(iter(make_dataloaders(batch_size=args.batch_size)["train"]))

    # 此处只查看输出，不需要记录梯度；后续训练分类头时不能照搬 no_grad。
    model.eval()
    with torch.no_grad():
        logits = model(images)
    trainable = [name for name, parameter in model.named_parameters()
                 if parameter.requires_grad]
    assert logits.shape == (len(images), len(CLASS_TO_IDX))
    assert torch.isfinite(logits).all().item()
    assert trainable == ["fc.weight", "fc.bias"]
    trainable_count = sum(p.numel() for p in model.parameters() if p.requires_grad)
    assert trainable_count == 1539
    report = {
        "architecture": "resnet18", "weights": WEIGHTS.name,
        "weights_url": WEIGHTS.url, "seed": 42, "device": "cpu",
        "class_to_idx": CLASS_TO_IDX,
        "input_shape": list(images.shape), "label_shape": list(labels.shape),
        "output_shape": list(logits.shape),
        "trainable_parameters": trainable, "trainable_parameter_count": trainable_count,
        "total_parameter_count": sum(p.numel() for p in model.parameters()),
        "first_three_logits": logits[:3].tolist(),
        "checks_passed": True, "training_performed": False,
    }
    output = PROJECT_DIR / "outputs" / "tables" / "model_summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"预训练权重：{WEIGHTS.name}；新分类头：{model.fc}")
    print(f"输入 {list(images.shape)} → 输出 {list(logits.shape)}")
    print(f"可训练参数：{trainable}，共 {trainable_count} 个")
    print(f"检查通过：{output}；新分类头尚未训练。")


if __name__ == "__main__":
    main()
