"""观察当前进程的路径、解释器与一个专用于本课的环境变量。"""

import os
from pathlib import Path
import sys


def main():
    print(f"当前工作目录 cwd: {Path.cwd()}")
    print(f"脚本文件: {Path(__file__).resolve()}")
    print(f"脚本目录: {Path(__file__).resolve().parent}")
    print(f"Python 解释器: {sys.executable}")
    print(f"Python 版本: {sys.version.split()[0]}")
    print(f"进程 PID: {os.getpid()}")
    print(f"父进程 PID: {os.getppid()}")
    print(f"S0_LESSON_LABEL: {os.environ.get('S0_LESSON_LABEL', '<未设置>')}")


if __name__ == "__main__":
    main()
