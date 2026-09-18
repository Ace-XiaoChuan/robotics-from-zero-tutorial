"""教学对照：相对路径按 cwd 查找，只有 cwd 符合约定时才读到样本。"""

from pathlib import Path
import sys


def main():
    # 这行故意保留对启动位置的依赖，供实验比较。
    input_path = Path("data/joint_states.csv")
    print(f"当前工作目录 cwd: {Path.cwd()}")
    print(f"实际查找位置: {input_path.resolve()}")

    try:
        content = input_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        print(f"读取失败: {exc}", file=sys.stderr)
        print("请比较当前工作目录与脚本目录；相对路径从 cwd 开始。", file=sys.stderr)
        return 1

    print(content, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
