cmake_minimum_required(VERSION 3.8)
project(hello_moveit)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(moveit_msgs REQUIRED)          # 新增
find_package(shape_msgs REQUIRED)           # 新增
find_package(moveit_ros_planning_interface REQUIRED)
find_package(moveit_visual_tools REQUIRED)
find_package(rviz_visual_tools REQUIRED)    # 新增
find_package(Eigen3 REQUIRED)
find_package(moveit_core REQUIRED)
find_package(moveit_task_constructor_core REQUIRED) # 新增
find_package(moveit_task_constructor_msgs REQUIRED) # 新增
find_package(tf2_geometry_msgs REQUIRED)
find_package(tf2_eigen REQUIRED)

# ---------------------------------------------------
# 1. 编译第一个可执行文件: hello_moveit
# ---------------------------------------------------
add_executable(hello_moveit src/hello_moveit.cpp)
target_include_directories(hello_moveit PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>)
target_compile_features(hello_moveit PUBLIC c_std_99 cxx_std_17)  # Require C99 and C++17

ament_target_dependencies(
  hello_moveit
  "rclcpp"
  "geometry_msgs"
  "moveit_msgs"
  "shape_msgs"
  "moveit_ros_planning_interface"
  "moveit_visual_tools"
  "rviz_visual_tools"
)

# ---------------------------------------------------
# 2. 编译第二个可执行文件: draw_line_and_circle
# ---------------------------------------------------
add_executable(draw_line_and_circle src/draw_line_and_circle.cpp)
target_include_directories(draw_line_and_circle PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
  ${EIGEN3_INCLUDE_DIR}
)
target_compile_features(draw_line_and_circle PUBLIC c_std_99 cxx_std_17)
target_link_libraries(draw_line_and_circle Eigen3::Eigen)
ament_target_dependencies(
  draw_line_and_circle
  "rclcpp"
  "geometry_msgs"
  "moveit_msgs"
  "shape_msgs"
  "moveit_ros_planning_interface"
  "moveit_visual_tools"
  "rviz_visual_tools"
)

# ---------------------------------------------------
# 3. 编译第三个可执行文件: pick_and_place
# ---------------------------------------------------
add_executable(pick_and_place src/pick_and_place.cpp)
target_include_directories(pick_and_place PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)
target_compile_features(pick_and_place PUBLIC c_std_99 cxx_std_17)

# 为 pick_and_place 添加依赖
ament_target_dependencies(
  pick_and_place
  "rclcpp"
  "geometry_msgs"
  "moveit_msgs"
  "shape_msgs"
  "moveit_core"
  "moveit_task_constructor_core" # 新增
  "moveit_task_constructor_msgs" # 新增
  "moveit_ros_planning_interface"
  "moveit_visual_tools"
  "rviz_visual_tools"
  "tf2_geometry_msgs"
  "tf2_eigen"
)

# ---------------------------------------------------
# 4. 安装设置：把三个可执行文件都安装到 lib 目录下
# ---------------------------------------------------
# 注意：在这里补充了 pick_and_place
install(TARGETS hello_moveit draw_line_and_circle pick_and_place
  DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
