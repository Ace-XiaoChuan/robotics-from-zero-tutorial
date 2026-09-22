"""按类别分层划分数据，只保存清单，不移动或复制图片。"""

import hashlib
import json
from collections import Counter
from pathlib import Path

import sklearn
from sklearn.model_selection import train_test_split


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SEED = 42


def main():
    source = DATA_DIR / "selected_samples.json"
    source_bytes = source.read_bytes()
    samples = json.loads(source_bytes)
    paths = [sample["path"] for sample in samples]
    if not samples or len(set(paths)) != len(paths):
        raise ValueError("清单为空或存在重复路径。")
    for sample in samples:
        if sample["label"] not in {"paper", "cardboard", "metal"}:
            raise ValueError(f"未知标签：{sample}")
        if not (DATA_DIR / sample["path"]).is_file():
            raise FileNotFoundError(sample["path"])

    # stratify 使用清单中已修正的标签，尽量保持各集合类别比例一致。
    # 先留出 30%，再平分成验证集和测试集；整数取整会带来少量比例差异。
    train, held_out = train_test_split(
        samples, test_size=0.30, random_state=SEED,
        stratify=[sample["label"] for sample in samples],
    )
    val, test = train_test_split(
        held_out, test_size=0.50, random_state=SEED,
        stratify=[sample["label"] for sample in held_out],
    )
    splits = {"train": train, "val": val, "test": test}

    # 保存之前确认：三个集合互不重叠，合起来恰好覆盖原清单。
    path_sets = {name: {sample["path"] for sample in rows}
                 for name, rows in splits.items()}
    assert not (path_sets["train"] & path_sets["val"])
    assert not (path_sets["train"] & path_sets["test"])
    assert not (path_sets["val"] & path_sets["test"])
    assert set.union(*path_sets.values()) == set(paths)
    assert sum(map(len, splits.values())) == len(samples)

    summary = {
        "source": source.name,
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "seed": SEED,
        "method": "stratified train_test_split: 70/30, then 50/50 of held-out",
        "sklearn_version": sklearn.__version__,
        "class_to_idx": {"paper": 0, "cardboard": 1, "metal": 2},
        "total": len(samples),
        "limitations": [
            "用户报告人工大致查看约 25%，未发现其他明显错标；不是全量标签审核。",
            "尚未检查近似图片或按物品分组；路径无重叠不代表没有近似图片泄漏。",
            "metal91.jpg 的原始跨类别标注冲突尚未复核，本次保留当前标签。",
        ],
        "splits": {},
    }
    for name, rows in splits.items():
        summary["splits"][name] = {
            "count": len(rows),
            "fraction": len(rows) / len(samples),
            "class_counts": dict(sorted(Counter(s["label"] for s in rows).items())),
        }

    output_dir = DATA_DIR / "splits"
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in {**splits, "summary": summary}.items():
        (output_dir / f"{name}.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    for name, stats in summary["splits"].items():
        print(f"{name}: {stats['count']} 张，{stats['class_counts']}")
    print(f"种子：{SEED}；清单保存至：{output_dir}")


if __name__ == "__main__":
    main()
