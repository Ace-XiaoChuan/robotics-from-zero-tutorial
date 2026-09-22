"""学习笔记：将已划分的 MNIST 数据准备成模型能读取的 batch。

阅读顺序：
1. make_dataloaders：读取划分索引，设置图片转换规则和分批取样规则。
2. inspect_batch：实际取一批数据，检查形状、类型和数值范围。
3. main：串起上述步骤，并把检查结果保存下来。

本文件只准备和检查数据，不定义或训练神经网络，也不读取官方测试集。
"""

import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms


# __file__ 是当前脚本的位置；向上两层得到 week06_pytorch_digits 目录。
# 这样即使从不同的工作目录启动脚本，也能找到同一份数据和索引。
PROJECT_DIR = Path(__file__).resolve().parents[1]
SPLIT_PATH = PROJECT_DIR / "outputs/tables/mnist_split_indices.json"


def make_dataloaders(batch_size: int = 64, seed: int = 42):
    """复用已保存的划分；seed 控制训练取样顺序，不重新划分数据。"""
    # 索引是图片在官方训练数据中的位置，从 0 开始，不是图片的数字标签。
    # 例如索引 100 指第 101 张图片，它的标签可能是 0～9 中的任意一个。
    split = json.loads(SPLIT_PATH.read_text(encoding="utf-8"))
    train_indices = split["train_indices"]
    validation_indices = split["validation_indices"]
    # 两组索引合并、排序后应恰好等于 0～59999：既不能重复，也不能遗漏。
    if (len(train_indices) != 50000 or len(validation_indices) != 10000
            or sorted(train_indices + validation_indices) != list(range(60000))):
        raise ValueError("划分索引必须无重复地覆盖 60,000 张图片，数量为 50,000/10,000。")

    # 对本地 uint8 灰度图片，ToTensor 将像素除以 255，并增加通道维。
    # 例如亮度 128 变为约 0.502；图片内容不变，形状从 [28, 28] 变为
    # [1, 28, 28]，其中 1 表示灰度图只有一个通道，数值类型变为 float32。
    # 这里先登记转换规则，实际访问 dataset[i] 时才转换那张图片。
    # train=True 指官方的 60,000 张训练部分（包含我们将用于验证的图片）；
    # download=False 表示使用本地文件。
    dataset = datasets.MNIST(
        PROJECT_DIR / "data", train=True,
        transform=transforms.ToTensor(), download=False,
    )
    # Subset 可以理解为一张“取哪些图片”的清单，不会复制或修改原始图片。
    # 访问子集的第 i 项时，会按清单找到原图，并一起返回转换后的图片和标签。
    train_dataset = Subset(dataset, train_indices)
    validation_dataset = Subset(dataset, validation_indices)
    # DataLoader 负责把单个 (image, label) 组成 (images, labels) 批次。
    # batch_size=64：每次取 64 张；不足 64 张的最后一批也保留（drop_last=False）。
    # shuffle=True：训练每轮重新打乱顺序，但不改变训练/验证的归属和标签配对。
    # num_workers=0：在当前进程取数据，初学时便于理解和排查问题。
    # 独立 Generator + 固定 seed：在相同环境和调用顺序下复现取样顺序。
    # 固定种子不表示每轮顺序相同：生成器状态会随取样推进。
    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, num_workers=0,
        drop_last=False, generator=torch.Generator().manual_seed(seed),
    )
    # 验证只检查学习效果，保持索引清单中的顺序即可（shuffle=False）。
    # 两个加载器使用相同的像素转换规则，保证输入的表示方式一致。
    validation_loader = DataLoader(
        validation_dataset, batch_size=batch_size, shuffle=False, num_workers=0,
        drop_last=False, generator=torch.Generator().manual_seed(seed),
    )
    return train_loader, validation_loader


def inspect_batch(loader: DataLoader) -> dict:
    """检查默认 batch_size=64 时的首批输入；不遍历整个数据集。"""
    # iter(loader) 创建一个逐批取数据的迭代器；next(...) 取它的第一批。
    # 这时才会取出图片、执行 ToTensor，并把图片和标签分别堆叠成张量。
    images, labels = next(iter(loader))
    # assert 是检查条件：不满足就报错停止，避免把不符合预期的数据交给模型。
    # 图片四维依次为：批次大小、通道数、高度、宽度；每张图片对应一个标签。
    assert images.shape == (64, 1, 28, 28)
    assert labels.shape == (64,)
    # 图片用浮点数参与计算；标签用整数表示类别，不需要除以 255。
    assert images.dtype == torch.float32 and labels.dtype == torch.int64
    # isfinite 排除 NaN（无效数值）和正负无穷；all 表示所有元素都要满足。
    assert bool(torch.isfinite(images).all())
    assert 0 <= float(images.min()) <= float(images.max()) <= 1
    assert bool(((labels >= 0) & (labels <= 9)).all())
    # len(loader.dataset) 是图片数，len(loader) 是走完一轮需要的批次数。
    # 将张量的形状、数值等转成普通 Python 数据，方便保存为 JSON 学习记录。
    return {
        "samples": len(loader.dataset), "batches_per_epoch": len(loader),
        "image_shape": list(images.shape), "label_shape": list(labels.shape),
        "image_dtype": str(images.dtype), "label_dtype": str(labels.dtype),
        "pixel_min": float(images.min()), "pixel_max": float(images.max()),
        "first_10_labels": labels[:10].tolist(), "checks_passed": True,
    }


def main() -> None:
    """直接运行脚本时，完成数据准备、抽查和结果保存。"""
    train_loader, validation_loader = make_dataloaders()
    # 将子集中的样本与原始图片对照，验证缩放和标签配对。
    for loader in (train_loader, validation_loader):
        subset = loader.dataset
        # 子集中的第 0 张图，不一定是官方训练数据中的第 0 张图。
        # 先查索引清单，才能找到它对应的原始图片和标签。
        original_index = subset.indices[0]
        image, label = subset[0]
        # 手动复现 ToTensor 的结果作为对照：
        # float() 转为浮点数，unsqueeze(0) 在最前面增加一个通道维，再除以 255。
        # .data 读取原始像素；subset[0] 则会经过前面登记的转换规则。
        expected = subset.dataset.data[original_index].float().unsqueeze(0) / 255
        assert torch.equal(image, expected)
        assert label == int(subset.dataset.targets[original_index])
    # 分别检查训练和验证首批，将结果汇总；这不是模型的准确率评估。
    # 检查会推进训练加载器的随机状态。正式训练时重新调用 make_dataloaders()
    # 创建加载器，即可从设定的随机状态开始，不受本次抽查影响。
    report = {
        "split_file": str(SPLIT_PATH.relative_to(PROJECT_DIR)),
        "shuffle_seed": 42, "batch_size": 64, "num_workers": 0,
        "train_shuffle": True, "validation_shuffle": False, "drop_last": False,
        "sample_scaling_and_label_alignment_checks_passed": True,
        "train": inspect_batch(train_loader),
        "validation": inspect_batch(validation_loader),
        "official_test_loaded": False,
    }
    # JSON 保存到文件，方便以后翻阅；print 同时把结果显示在终端。
    output = PROJECT_DIR / "outputs/tables/dataloader_inspection.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


# 直接运行 python src/data.py 时执行 main；以后训练文件导入本模块时，
# 只提供函数定义，不自动运行检查或写入报告。
if __name__ == "__main__":
    main()
