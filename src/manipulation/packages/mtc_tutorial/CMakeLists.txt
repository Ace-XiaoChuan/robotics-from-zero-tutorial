cmake_minimum_required(VERSION 3.8)
project(mtc_tutorial)

# 建议直接在项目层面设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(moveit_task_constructor_core REQUIRED)
find_package(rclcpp REQUIRED)
find_package(moveit_core REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)

# --- 1. 处理可执行文件 ---
add_executable(mtc_node src/mtc_node.cpp)

target_include_directories(mtc_node PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)

ament_target_dependencies(
  mtc_node
  moveit_task_constructor_core
  rclcpp
  moveit_core
  moveit_ros_planning_interface
)

# --- 2. 安装部分 (这是你关心的部分) ---

# 安装二进制文件到 lib 下
install(TARGETS mtc_node
  DESTINATION lib/${PROJECT_NAME})

# 安装 launch 文件夹及其内容到 share 下
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME})

# 如果未来你有 config 文件夹（放置 RViz 配置或 YAML 参数），也记得加上这行：
# install(DIRECTORY config DESTINATION share/${PROJECT_NAME})

# --- 3. 测试与打包 ---
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()