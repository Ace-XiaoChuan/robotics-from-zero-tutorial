"""更新学习文档顶部的行数与粗略阅读时长；--check 只检查，不写入。"""

import argparse
import math
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
METADATA = re.compile(r"^本文行数：\d+行，预期阅读时长：\d+分钟$")
PLACEHOLDER = "本文行数：<实际行数>行，预期阅读时长：<估算分钟数>分钟"
SKIP_DIRS = {"build", "install", "log", "__pycache__", "node_modules", "venv"}


def documents():
    candidates = list(ROOT.glob("*.md"))
    for folder in ("doc", "src"):
        candidates.extend((ROOT / folder).rglob("*.md"))
    return sorted(
        path for path in candidates
        if not path.is_symlink()
        and not any(
            part.startswith(".") or part in SKIP_DIRS
            for part in path.relative_to(ROOT).parts
        )
    )


def updated_text(original):
    lines = original.splitlines()
    first = next((i for i, line in enumerate(lines) if line.strip()), len(lines))
    # 只检查文首标题之后的位置，不改动代码块内的样板说明。
    position = first + 1 if first < len(lines) and lines[first].startswith("# ") else first
    while position < len(lines) and not lines[position].strip():
        position += 1
    if position < len(lines) and (
        METADATA.fullmatch(lines[position]) or lines[position] == PLACEHOLDER
    ):
        lines[position] = ""
    else:
        insertion = ["", ""]
        if position > 0 and lines[position - 1].strip():
            insertion.insert(0, "")
            lines[position:position] = insertion
            position += 1
        else:
            lines[position:position] = insertion

    content = "\n".join(lines)
    content = re.sub(r"https?://[^\s<>\)]+", "", content)
    chinese = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]", content))
    words = len(re.findall(r"[A-Za-z0-9]+(?:[_'-][A-Za-z0-9]+)*", content))
    minutes = max(1, math.ceil(chinese / 400 + words / 200))
    lines[position] = f"本文行数：{len(lines)}行，预期阅读时长：{minutes}分钟"
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="只检查统计是否过期")
    args = parser.parse_args()
    paths = documents()
    changed = 0
    for path in paths:
        original = path.read_text(encoding="utf-8")
        updated = updated_text(original)
        if updated != original:
            changed += 1
            if not args.check:
                path.write_text(updated, encoding="utf-8")
            print(f"{'待更新' if args.check else '已更新'}：{path.relative_to(ROOT)}")
    print(f"共检查 {len(paths)} 篇文档，{'待更新' if args.check else '更新'} {changed} 篇。")
    return int(args.check and changed > 0)


if __name__ == "__main__":
    raise SystemExit(main())
