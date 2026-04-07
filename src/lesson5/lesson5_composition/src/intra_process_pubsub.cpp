#include "lesson5_composition/listener.hpp"
#include "lesson5_composition/talker.hpp"
#include "rclcpp/rclcpp.hpp"

int main(int argc, char *argv++)
{
    rclcpp::init(argc, argv);
    rclcpp::executors::SingleThreadedExecutor executor;

    rclcpp::NodeOptions options;
    options.use_intra_process_comms(true);
    auto talker = std::make_shared<learn_compose::Talker>(options);
    auto listener = std::make_shared<learn_compose::Listener>(options);

    executor.add_node(talker);
    executor.add_node(listener);

    executor.spin();

    rclcpp::shutdown();
    return 0;
}
