"""内置样本相对脚本查找；显式 --input 路径相对调用者 cwd 解释。"""

import argparse
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(
        description="读取一个小型 UTF-8 文本文件，观察路径的解释方式。"
    )
    parser.add_argument(
        "--input",
        metavar="PATH",
        help="输入文件；相对路径基于当前工作目录，支持 ~；省略时读取内置样本",
    )
    args = parser.parse_args()

    if args.input is None:
        # 随脚本附带的资源与脚本一起移动，不能依赖调用者的 cwd。
        raw_path = Path(__file__).resolve().parent / "data" / "joint_states.csv"
        source = "内置样本（相对脚本目录）"
    else:
        # 用户主动传入的路径按命令行的常见约定解释：相对 cwd。
        raw_path = Path(args.input)
        source = "--input（相对路径基于 cwd）"

    print(f"当前工作目录 cwd: {Path.cwd()}")
    print(f"输入来源: {source}")
    try:
        input_path = raw_path.expanduser().resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"路径解析失败: {raw_path}；{exc}", file=sys.stderr)
        return 1

    print(f"实际读取路径: {input_path}")
    try:
        content = input_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"文件不存在: {input_path}", file=sys.stderr)
        print("检查 --input 的拼写及 cwd；相对路径不会自动按脚本目录查找。", file=sys.stderr)
        return 1
    except IsADirectoryError:
        print(f"输入是目录，请指定文件: {input_path}", file=sys.stderr)
        return 1
    except PermissionError:
        print(f"没有读取权限: {input_path}", file=sys.stderr)
        return 1
    except UnicodeError:
        print(f"输入不是有效的 UTF-8 文本: {input_path}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"无法读取 {input_path}: {exc}", file=sys.stderr)
        return 1

    print(content, end="" if content.endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
