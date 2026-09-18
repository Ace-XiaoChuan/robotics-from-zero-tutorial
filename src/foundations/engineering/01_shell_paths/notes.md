# 终端与路径：遇到问题再查

本文行数：86行，预期阅读时长：3分钟

日常学习只需阅读 [单元入口](README.md)。这里按症状查，不要求通读或背诵。

<a id="paths"></a>

## 1. 文件找不到

先看 `pwd` 和报错里的实际路径。

| 写法 | 从哪里找 |
| --- | --- |
| `/某处/data.csv` | 绝对路径，直接指向该位置 |
| `data/data.csv` | 通常从当前工作目录开始 |
| `../data.csv` | 当前目录的上一级 |

**用绝对路径启动脚本，不会自动切换到脚本目录。**

<a id="file-policy"></a>

### 让 AI 修改路径时，说明你的意图

- 随脚本附带的小样本：相对脚本定位，例如 `Path(__file__).resolve().parent / "data" / "joint_states.csv"`。
- 用户选择的模型或数据：通过参数指定，明确相对路径的起点。
- 输入文件不存在：报错并显示路径，避免偷偷换成另一份默认数据。

这些是本课普通 Python 脚本的约定，API 需要时查 [pathlib 文档](https://docs.python.org/3.10/library/pathlib.html)。

<a id="commands"></a>

## 2. IDE 能运行，终端不能运行

比较工作目录、Python 解释器、参数和环境。在两个运行方式中打印信息，再对比：

```python
import os
import sys
print(os.getcwd())
print(sys.executable)
```

`PATH` 主要影响外部命令查找，不能代替数据文件路径。解释器字段的含义见 [sys.executable](https://docs.python.org/3.10/library/sys.html#sys.executable)。

<a id="quoting"></a>

## 3. 路径带空格后报参数错误

给整个路径加双引号，例如 `--input "data/joint states.csv"`。引用路径变量也写成 `"$s0_unit"`，让路径保持为一个参数。

<a id="shell"></a>
<a id="environment"></a>
<a id="source"></a>

## 4. 环境设置了却不生效

- `export 名称=值`：让之后启动的子程序获得该环境变量。
- `source 环境脚本.sh`：在当前终端的 Shell 中加载设置。
- `bash 环境脚本.sh`：在子 Shell 中执行，变量修改不会自动传回当前 Shell。
- 换一个终端，通常需要重新加载对应环境；已经运行的程序也不会自动更新环境。

先按项目说明加载环境，不需要为了这一节掌握进程细节。需要深究时用 Bash 的 `help source`、`help export` 查本机帮助。

<a id="errors"></a>

## 5. 根据报错决定查哪里

| 报错或现象 | 优先检查 |
| --- | --- |
| `command not found` | 命令是否安装、终端环境 |
| Python `can't open file` | 脚本路径与工作目录 |
| 本课“文件不存在” | 输入参数与实际数据位置 |
| `ModuleNotFoundError` | 实际 Python 解释器与依赖 |
| `unrecognized arguments` | 参数拼写、路径引号 |
| `Permission denied` | 文件权限与要执行的操作 |

程序退出码一般以 0 表示成功，非 0 表示错误；具体含义看程序约定。本课读取失败返回 1，参数错误返回 2，无需背诵。

<a id="review"></a>

## 6. 交给 AI 排查时提供什么

提供启动目录、完整命令、完整报错、预期文件位置和实际解释器。让 AI 说明改了什么，再运行确认读取的文件与结果符合预期。

语法和配置可以随用随查；自己保留对任务目标、输入文件和运行结果的判断。
