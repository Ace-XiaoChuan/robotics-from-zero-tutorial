# S0 · 单元 04：C++ 与构建

本文行数：103行，预期阅读时长：4分钟

**一句话回忆：C++ 源码要先编译成目标文件，再链接成可执行程序；CMake 描述构建关系，`colcon build` 负责在 ROS 2 工作区批量调用它。**

## 速记

- 编译（compile）把一个 `.cpp` 翻译成目标文件；链接（link）把目标文件和库组合成可执行文件。报错位置通常能帮助区分这两步。
- 头文件提供声明，源文件提供定义。声明找不到常见于 `#include` 或 include 路径问题；`undefined reference` 常见于定义没有参与链接。
- CMake 的 `target` 是依赖边界：用 `target_sources`、`target_include_directories`、`target_link_libraries` 描述一个程序需要什么。
- `Debug` 便于断点和变量检查，`Release` 更关注优化；不要把一次构建目录中的缓存选项当作永久配置。
- ROS 2 包通常由 `colcon build --symlink-install` 构建；运行前要在当前终端 `source install/setup.bash`，否则可能找不到新包或仍使用旧版本。

## 例子：从一个 C++ 文件生成程序

**条件 / 输入：** `hello.cpp`：

```cpp
#include <iostream>

int main() {
  std::cout << "joints: 7\\n";
  return 0;
}
```

直接构建可以写成：

```bash
g++ -std=c++17 -Wall -Wextra hello.cpp -o hello
./hello
```

**结果：** 终端输出 `joints: 7`，并生成名为 `hello` 的可执行文件。`-Wall -Wextra` 会把许多潜在问题作为警告显示出来；警告不等于程序已经完成语义验证。

**解释：** `-std=c++17` 固定语言标准，避免换机器后编译器按不同默认标准解释源码；`-o hello` 明确输出文件名。这里的 `7` 只是教学示意，不代表某个实际机械臂接口。

结果依据：命令和输出是可直接复现的教学例子，不是仓库中某个 ROS 节点的实测结果。

## 例子：用 CMake 表达构建关系

目录可以只有两个文件：

```text
cpp_demo/
├── CMakeLists.txt
└── src/hello.cpp
```

最小 `CMakeLists.txt`：

```cmake
cmake_minimum_required(VERSION 3.16)
project(cpp_demo LANGUAGES CXX)

add_executable(hello src/hello.cpp)
target_compile_features(hello PRIVATE cxx_std_17)
target_compile_options(hello PRIVATE -Wall -Wextra)
```

配置和构建：

```bash
cmake -S cpp_demo -B cpp_demo/build -DCMAKE_BUILD_TYPE=Debug
cmake --build cpp_demo/build --parallel
./cpp_demo/build/hello
```

**结果：** CMake 在 `build/` 中生成构建系统，随后产出 `build/hello`。修改 `hello.cpp` 后再次执行 `cmake --build` 通常只重编译受影响的目标。

**解释：** `-S` 指源码目录，`-B` 指构建目录；把产物放在源码外可以减少目录污染，也便于删除缓存后重新配置。`project()` 名称不决定可执行文件名，`add_executable()` 的第一个参数才是 target 名称。

## ROS 2 中怎样对应

`ament_cmake` 包仍然使用同一套 CMake target 规则，只是由 `colcon` 从工作区根目录统一调度：

```bash
colcon build --packages-select <package_name> --symlink-install
source install/setup.bash
ros2 run <package_name> <executable_name>
```

**结果与解释：** `--packages-select` 缩小构建范围；`--symlink-install` 让 Python 文件和部分资源修改更快生效，但 C++ 源码仍需重新编译。每次新开终端都要重新 source；source 只改变当前 shell 的环境，不会修改源码或构建产物。

## 遇到问题时查

| 现象 | 原因或检查方向 |
| --- | --- |
| `fatal error: xxx.hpp: No such file` | 检查 `#include` 拼写、头文件是否安装，以及 target 的 include 目录和依赖声明 |
| `undefined reference to ...` | 声明可见但实现未链接；检查源文件是否加入 target、库是否加入 `target_link_libraries` |
| 修改后运行结果没变 | 确认重新构建、运行的是当前 build/install 下的程序，并重新 source 工作区 |
| CMake 仍使用旧编译器或选项 | 删除对应 `build/` 目录后重新 `cmake -S ... -B ...`；先记录原配置再清理 |
| `colcon build` 在其他包失败 | 先看第一个真正的编译/链接错误；用 `--packages-select` 隔离目标包，避免被后续连锁报错干扰 |
| 运行时找不到共享库 | 检查 `install/setup.bash` 是否已 source，以及库 target 是否正确安装和导出 |

## 需要深入时

- [CMake Tutorial](https://cmake.org/cmake/help/latest/guide/tutorial/index.html)：从 target、依赖和安装规则开始。
- [ROS 2 Humble 创建 ament_cmake 包](https://docs.ros.org/en/humble/How-To-Guides/Ament-CMake-Documentation.html)：核对 `ament_target_dependencies`、安装和导出约定。
- 本仓库的 [Lesson 2 组件构建案例](../../../lesson2/lesson2_composition/CMakeLists.txt)：查看真实 ROS 2 C++ 包的 `CMakeLists.txt`、头文件和可执行目标。

返回 [S0 索引](../README.md) · [学习路线](../../../../doc/learning-roadmap.md#s0)。
