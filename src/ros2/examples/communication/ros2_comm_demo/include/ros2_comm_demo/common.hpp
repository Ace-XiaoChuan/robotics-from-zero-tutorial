#pragma once
#include <chrono>
#include <cmath>
#include <memory>
#include <stdexcept>
#include <string>
#include "rclcpp/rclcpp.hpp"
#include "rcl_interfaces/msg/parameter_descriptor.hpp"

namespace demo {
using Clock = std::chrono::steady_clock;
inline double elapsed(Clock::time_point since) {
  return std::chrono::duration<double>(Clock::now() - since).count();
}
// Parameters are startup-only: updating a value must not silently leave an old timer running.
template<class T>
T parameter(rclcpp::Node & node, const std::string & name, T value) {
  rcl_interfaces::msg::ParameterDescriptor descriptor;
  descriptor.read_only = true;
  return node.declare_parameter<T>(name, value, descriptor);
}
inline double positive(rclcpp::Node & node, const std::string & name, double value) {
  const auto result = parameter(node, name, value);
  if (!std::isfinite(result) || result < 0.001) {
    throw std::invalid_argument(name + " must be finite and >= 0.001");
  }
  return result;
}
inline auto period(double seconds) {
  return std::chrono::duration_cast<std::chrono::nanoseconds>(
    std::chrono::duration<double>(seconds));
}
inline void require_wall_time(rclcpp::Node & node) {
  if (node.get_parameter("use_sim_time").as_bool()) {
    throw std::invalid_argument("This standalone demo requires use_sim_time=false");
  }
}
template<class Node> int run(int argc, char ** argv) {
  rclcpp::init(argc, argv);
  try {
    rclcpp::spin(std::make_shared<Node>());
  } catch (const std::exception & e) {
    RCLCPP_FATAL(rclcpp::get_logger("lesson1"), "%s", e.what());
    rclcpp::shutdown();
    return 1;
  }
  rclcpp::shutdown();
  return 0;
}
}  // namespace demo
