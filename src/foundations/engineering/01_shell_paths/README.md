# S0 · 单元 01：运行位置与文件路径

本文行数：54行，预期阅读时长：2分钟

**快速回忆：文件找不到，先看程序从哪里启动、实际在找哪条路径。** 以下例子直接给出结果，无需执行。

## 记住这四点

- **当前工作目录（cwd）**：程序查找普通相对路径的起点，终端里用 `pwd` 查看。
- **脚本目录**：代码文件存放的位置，不一定等于 cwd。
- **输入路径**：通常用 `--input` 等参数指定，带空格时加双引号。
- **运行环境**：换个终端出错，比较工作目录、Python 解释器和加载的环境。

## 例子 1：同一行代码为什么有时成功、有时失败

本单元的文件结构是：

```text
01_shell_paths/
├── read_relative.py
└── data/joint_states.csv
```

代码读取 `data/joint_states.csv`，结果取决于启动位置：

| 从哪里启动 | 实际查找位置 | 当前仓库中的结果 |
| --- | --- | --- |
| 仓库根目录 | 仓库根目录下的 `data/joint_states.csv` | 文件不在那里，读取失败 |
| `01_shell_paths/` 目录 | 本单元的 `data/joint_states.csv` | 成功读取两行样本数据 |

**原因：相对路径从 cwd 出发。即使使用绝对路径指定脚本，也不会自动切换 cwd。**

## 例子 2：程序应该怎样选择输入文件

[read_file.py](read_file.py) 使用下面的约定。表中命令假设从单元目录启动：

| 用法 | 结果与含义 |
| --- | --- |
| `python3 read_file.py` | 读取脚本旁的内置样本，换 cwd 也能找到它 |
| `python3 read_file.py --input data/joint_states.csv` | 按调用者的 cwd 查找指定文件 |
| `python3 read_file.py --input data/missing.csv` | 报“文件不存在”，显示实际路径，不偷偷换用默认数据 |
| `--input "joint states.csv"` | 双引号让带空格的路径作为一个参数传入；文件仍需实际存在 |

**记住选择规则即可：内置资源随代码定位，用户数据由参数明确指定。** 具体实现可以交给 agent。

## 遇到问题时怎样描述

> 我从……目录启动，完整命令是……，想读取的文件在……，实际报错是……。请定位原因并给出最小修改。

需要时查 [排错速查](notes.md)。配套 [路径示例](read_relative.py)、[环境观察](inspect_context.py)、[环境设置示例](set_lesson_env.sh)和 [自动检查](test_examples.py)供实现参考，不是复习作业。

验证依据：配套代码此前在 Linux / Bash 5.1.16 / Python 3.10.12 下通过 10 项自动检查。本文只将阅读方式改为例子与结论。

返回 [S0 索引](../README.md) · [学习路线](../../../../doc/learning-roadmap.md#s0)。
