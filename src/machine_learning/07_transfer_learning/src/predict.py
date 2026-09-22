"""加载本周保存的完整模型，对一张本地照片进行三分类推理。"""

import argparse
from pathlib import Path

import torch
from PIL import Image, ImageOps, UnidentifiedImageError
from torch import nn
from torchvision import transforms
from torchvision.models import resnet18

from data import CLASS_TO_IDX, PROJECT_DIR


def predict(image_path, checkpoint_path):
    # 检查点含骨干与分类头全部参数，不需要联网，也不会重新训练。
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    metadata = checkpoint["metadata"]
    if metadata["architecture"] != "resnet18" or metadata["class_to_idx"] != CLASS_TO_IDX:
        raise ValueError("模型结构或类别映射与本周项目不一致。")
    model = resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, len(CLASS_TO_IDX))
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.eval()  # BatchNorm 使用训练时保存的统计量，不根据这张照片更新。

    # 从检查点还原固定预处理，保持与评估一致；推理不做随机增强。
    config = metadata["preprocessing"]
    preprocess = transforms.Compose([
        transforms.Resize(config["resize_size"],
                          interpolation=transforms.InterpolationMode(config["interpolation"]),
                          antialias=config["antialias"]),
        transforms.CenterCrop(config["crop_size"]),
        transforms.ToTensor(),
        transforms.Normalize(config["mean"], config["std"]),
    ])
    with Image.open(image_path) as original:
        # 手机照片有时通过 EXIF 标记方向，而像素本身还是横着的。
        # 先修正显示方向再转 RGB；只处理内存中的副本，不修改原文件。
        image = ImageOps.exif_transpose(original).convert("RGB")
        # 单张为 [3,224,224]，加一个批次维度后成为模型要求的 [1,3,224,224]。
        inputs = preprocess(image).unsqueeze(0)
    with torch.inference_mode():
        logits = model(inputs)
        if not torch.isfinite(logits).all():
            raise ValueError("模型输出包含非有限值。")
        # softmax 把三类分数转为总和为 1 的概率形式，不能当作可靠性保证。
        probabilities = logits.softmax(dim=1)[0].tolist()
    return {name: probabilities[index] for name, index in CLASS_TO_IDX.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path, help="照片路径（支持 JPG、PNG 等 Pillow 可读取格式）")
    parser.add_argument("--checkpoint", type=Path,
                        default=PROJECT_DIR / "outputs/runs/20260921_augmented/best_model.pt",
                        help="完整模型文件路径，默认使用增强版第 3 轮模型")
    args = parser.parse_args()
    torch.set_num_threads(2)
    try:
        scores = predict(args.image.expanduser(), args.checkpoint.expanduser())
    except (OSError, UnidentifiedImageError, ValueError) as error:
        parser.exit(1, f"无法完成推理：{error}\n请检查照片/模型路径；手机 HEIC 照片可先导出为 JPG。\n")
    names = {"paper": "纸张", "cardboard": "纸板", "metal": "金属"}
    ranking = sorted(scores, key=scores.get, reverse=True)
    print(f"预测类别：{names[ranking[0]]}（{ranking[0]}）")
    for name in ranking:
        print(f"  {names[name]}（{name}）：{scores[name]:.2%}")
    print("以上为三类 softmax 分数；模型不能自动识别‘其他物品’，高分也可能预测错误。")


if __name__ == "__main__":
    main()
