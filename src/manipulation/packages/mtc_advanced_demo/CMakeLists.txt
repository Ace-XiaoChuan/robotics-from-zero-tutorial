cmake_minimum_required(VERSION 3.8)
project(mtc_advanced_demo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 寻找构建依赖
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(shape_msgs REQUIRED)
find_package(moveit_msgs REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(moveit_task_constructor_core REQUIRED)

# -----------------------------------------------------------
# 1. 创建可执行文件并添加所有对应的 cpp 源码文件
# 假设你的 cpp 文件都存放在 src/ 目录下
# -----------------------------------------------------------
add_executable(mtc_node
  src/main.cpp
  src/environment_manager.cpp
  src/robot_app_controller.cpp
  src/task_builder.cpp
)

# -----------------------------------------------------------
# 2. 设置头文件包含目录（解决你之前找不到头文件的问题）
# -----------------------------------------------------------
target_include_directories(mtc_node PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

# -----------------------------------------------------------
# 3. 链接所有找到的 ROS 2 库
# -----------------------------------------------------------
ament_target_dependencies(mtc_node
  rclcpp
  geometry_msgs
  shape_msgs
  moveit_msgs
  moveit_ros_planning_interface
  moveit_task_constructor_core
)

# -----------------------------------------------------------
# 4. 安装规则（为了让 ros2 run 能找到节点）
# -----------------------------------------------------------
install(TARGETS mtc_node
  DESTINATION lib/${PROJECT_NAME}
)

# 安装 launch 或 config 文件夹（如果你有的话，没有可保留或注释掉）
# install(DIRECTORY launch
#   DESTINATION share/${PROJECT_NAME}
# )

ament_package()