#include <iostream>
#include <vector>
#include <string>
#include <cctype>

// 创建一个 vector<string>，存入 5 个城市名
// 用 auto + 范围for 遍历并打印每个城市
// 用 auto + 范围for（引用方式）把每个城市名转成大写，再打印一遍
// 禁止出现任何显式类型声明（除了第一行 vector 的创建）

int main()
{
    // 1.创建一个vector<string>，这是唯一允许出现显式类型声明的一行
    std::vector<std::string> cities = {"beijing", "shanghai", "tokyo", "london", "paris"};
    // 2. 用 auto + 范围for 遍历并打印每个城市 (按值传递)
    for (auto city : cities)
    {
        std::cout << city << " ";
    }
    std::cout << "\n";

    // 3. 用 auto& + 范围for（引用方式）把每个城市名转成大写，再打印一遍
    for (auto &city : cities)
    {
        for (auto &c : city)
        {
            c = std::toupper(c);
        }
        std::cout << city << " ";
    }
    std::cout << "\n";
    return 0;
}
