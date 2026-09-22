"""读取固定划分，提供单张 Dataset 和批量 DataLoader；不下载模型。"""

import argparse
import json
from pathlib import Path

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from torchvision.models import ResNet18_Weights


PROJECT_DIR = Path(__file__).resolve().parents[1]
CLASS_TO_IDX = {"paper": 0, "cardboard": 1, "metal": 2}
TRAIN_AUGMENTATION = {"horizontal_flip_probability": 0.5,
                      "brightness": 0.1, "contrast": 0.1}


def build_transform(training=False):
    """训练可使用随机增强；默认返回验证、测试和推理的固定预处理。"""
    # 只创建预处理，不会下载或加载模型权重。
    # 短边缩放到 256 → 中心裁剪 224×224 → 浮点张量 → 按通道标准化。
    # 标准化后可以有负数，也可以大于 1，不再是探索阶段的 [0, 1]。
    preprocess = ResNet18_Weights.IMAGENET1K_V1.transforms()
    if not training:
        return preprocess
    # Compose 按列表顺序执行。先对内存中的 RGB 图片增强，再交给官方预处理。
    # 不保存修改后的图片，不覆盖原图，也不改变标签或每轮样本数量。
    return transforms.Compose([
        # 每次读图独立决定是否左右翻转：概率 50%，不是固定翻转一半数据。
        # 对本项目的材料分类，左右翻转通常不会改变“纸张/纸板/金属”类别。
        transforms.RandomHorizontalFlip(p=TRAIN_AUGMENTATION["horizontal_flip_probability"]),
        # 0.1 表示因子从 [0.9, 1.1] 随机抽取，不是给每个像素加 0.1。
        # 亮度因子 <1 变暗、>1 变亮；对比度因子 <1 变平淡、>1 明暗差异变大。
        # 两个因子分别抽取，执行先后也随机；不调整饱和度和色相。
        # 这些是轻微的外观扰动，不能等同于完整模拟相机曝光变化。
        transforms.ColorJitter(brightness=TRAIN_AUGMENTATION["brightness"],
                               contrast=TRAIN_AUGMENTATION["contrast"]),
        # 沿用固定缩放和中心裁剪，不新增随机裁剪；中心裁剪仍可能舍去边缘。
        # 亮度/对比度在标准化之前调整，避免把标准化后的数值当作普通像素。
        preprocess,
    ])


class TrashDataset(Dataset):
    """废弃物图片数据集。Dataset 管单张：按清单索引返回 (图片张量, 类别编号)。"""

    def __init__(self, split, data_dir=PROJECT_DIR / "data", transform=None,
                 augment=True):
        if split not in {"train", "val", "test"}:
            raise ValueError("split 必须是 train、val 或 test。")
        self.data_dir = Path(data_dir)
        self.samples = json.loads(
            (self.data_dir / "splits" / f"{split}.json").read_text(encoding="utf-8")
        )
        if not self.samples:
            raise ValueError(f"{split} 清单为空。")
        # 只有训练集默认增强；验证/测试固定处理，便于公平比较模型成绩。
        # augment=False 可关闭训练增强、复现旧基线。显式传 transform 时以它为准。
        self.transform = (build_transform(training=(split == "train" and augment))
                          if transform is None else transform)
        for sample in self.samples:
            if sample["label"] not in CLASS_TO_IDX:
                raise ValueError(f"未知标签：{sample['label']}")
            if not (self.data_dir / sample["path"]).is_file():
                raise FileNotFoundError(sample["path"])

    def __len__(self):
        # len(dataset) 是这个集合中的图片数。
        return len(self.samples)

    def __getitem__(self, index):
        # 初始化时只读清单；真正访问某一项时才读取和转换这张图片。
        sample = self.samples[index]
        with Image.open(self.data_dir / sample["path"]) as image:
            # 每次 __getitem__ 都重新抽取增强参数，同一张图跨轮次可能外观不同。
            tensor = self.transform(image.convert("RGB"))
        # 用清单标签，不用文件夹名；paper201.jpg 的修正标签因此仍是 metal。
        label = CLASS_TO_IDX[sample["label"]]
        return tensor, label


def make_dataloaders(batch_size=32, seed=42, data_dir=PROJECT_DIR / "data", augment=True):
    """返回 train、val、test 三个加载器，供后续训练和评估代码调用。"""
    if batch_size < 1:
        raise ValueError("batch_size 必须为正整数。")
    loaders = {}
    for split in ("train", "val", "test"):
        loaders[split] = DataLoader(
            TrashDataset(split, data_dir=data_dir, augment=augment),
            batch_size=batch_size,
            # 只打乱训练集的取样顺序，不改变划分归属或图片与标签的配对。
            shuffle=(split == "train"),
            num_workers=0,  # 在当前进程加载，便于初学时调试。
            drop_last=False,  # 最后一批不足 batch_size 也保留。
            # 每个加载器使用独立生成器；训练每轮顺序不同，但可复现。
            # num_workers=0 时，随机增强使用全局 torch 随机状态；调用方还需
            # 在运行开始设 torch.manual_seed(seed)，且不要每批/每轮重设种子。
            generator=torch.Generator().manual_seed(seed),
        )
    return loaders


def inspect_loaders(loaders):
    """仅检查各集合第一批的数据格式，不做预测、不计算测试集成绩。"""
    report = {}
    for split, loader in loaders.items():
        images, labels = next(iter(loader))
        expected = min(loader.batch_size, len(loader.dataset))
        assert images.shape == (expected, 3, 224, 224)
        assert labels.shape == (expected,)
        assert images.dtype == torch.float32 and labels.dtype == torch.int64
        assert torch.isfinite(images).all().item()
        assert ((labels >= 0) & (labels < 3)).all().item()
        report[split] = {
            "samples": len(loader.dataset),
            "batches": len(loader),
            "first_image_shape": list(images.shape),
            "first_label_shape": list(labels.shape),
            "image_dtype": str(images.dtype),
            "label_dtype": str(labels.dtype),
            "first_batch_range": [images.min().item(), images.max().item()],
            "last_batch_size": (len(loader.dataset) - 1) % loader.batch_size + 1,
        }
        print(f"{split}: {len(loader.dataset)} 张，{len(loader)} 批；"
              f"images={list(images.shape)}，labels={list(labels.shape)}；"
              f"最后一批 {report[split]['last_batch_size']} 张")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    # 仅限制此演示程序的 CPU 线程数，避免小张量运算启动过多线程。
    torch.set_num_threads(2)
    torch.manual_seed(42)
    loaders = make_dataloaders(batch_size=args.batch_size)
    report = {
        "batch_size": args.batch_size, "seed": 42, "class_to_idx": CLASS_TO_IDX,
        "preprocessing": str(build_transform()),
        "random_augmentation": {"train": TRAIN_AUGMENTATION, "val": False, "test": False},
        "splits": inspect_loaders(loaders),
    }
    output = PROJECT_DIR / "outputs" / "tables" / "dataloader_summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(f"检查通过，记录：{output}")


if __name__ == "__main__":
    main()
