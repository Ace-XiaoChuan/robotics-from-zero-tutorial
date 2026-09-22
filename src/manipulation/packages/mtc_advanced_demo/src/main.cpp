#include <rclcpp/rclcpp.hpp>
#include "mtc_advanced_demo/robot_app_controller.hpp"
#include <thread>

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);

    // rclcpp::NodeOptions 是 ROS 2 中用来配置节点的**“属性大管家”**，主要掌管四大核心能力
    // 1. 允许外部参数动态覆盖2. ROS 2 组件化 (Components) 的通行证3. 开启“零拷贝”进程内通信4. 话题重映射与参数初始化
    rclcpp::NodeOptions options;
    // 允许从启动文件或命令行覆盖参数（MoveIt 必须）
    options.automatically_declare_parameters_from_overrides(true);

    // 实例化控制器
    auto app_controller = std::make_shared<mtc_advanced_demo::RobotAppController>(options);

    // 创建多线程执行器（MTC 在规划时需要与 MoveGroup 节点进行后台通信）
    rclcpp::executors::MultiThreadedExecutor executor;

    // 构造即启动。这行代码中的线程在它被创建的瞬间，立刻就会开始执行
    // 支线线程会立即开始执行.spin()
    auto spin_thread = std::make_unique<std::thread>([&executor, &app_controller]()
                                                     {
                                                        // 把节点挂载到执行器（Executor）上让它开始处理回调，以及在结束时卸载。
        executor.add_node(app_controller->getNodeBaseInterface());
        executor.spin();
        executor.remove_node(app_controller->getNodeBaseInterface()); });

    // 运行核心流水线
    app_controller->run();

    // 等待线程结束并清理资源
    spin_thread->join();
    rclcpp::shutdown();
    return 0;
}