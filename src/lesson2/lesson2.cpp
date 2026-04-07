// 【要求】
// 1. 创建 vector<int> v = {3, 1, 4, 1, 5, 9, 2, 6}
// 2. 用 lambda 配合 std::sort 实现降序排序，打印结果
// 3. 用 lambda 配合 std::sort 实现 "偶数在前、奇数在后，同类内部升序 ",打印结果
// 4. 用 std::count_if + lambda 统计大于4的元素个数并打印

// 【预期输出】
// 降序 : 9 6 5 4 3 2 1 1 分类 : 2 4 6 1 1 3 5 9 大于4的个数 : 3

#include <iostream>
#include <vector>
#include <algorithm>

int main()
{
    std::vector<int> v = {3, 1, 4, 1, 5, 9, 2, 6};

    std::sort(v.begin(), v.end(), [](int a, int b)
              { return a > b; });
    std::cout << "降序: ";
    for (auto i : v)
    {
        std::cout << i << " ";
    };
    std::cout << std::endl;

    std::sort(v.begin(), v.end(), [](int a, int b)
              {
        if(a % 2 != b % 2){
            return a % 2 < b % 2;
        }
        return a < b; });

    std::cout << "分类: ";
    for (int n : v)
        std::cout << n << " ";
    std::cout << std::endl;

    int count = std::count_if(v.begin(), v.end(), [](int n)
                              { return n > 4; });
    std::cout << "大于4的个数: " << count << std::endl;
    return 0;
}
