cmake_minimum_required(VERSION 3.8)
project(ros2_comm_demo)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(robot_interfaces REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(std_msgs REQUIRED)

set(NODES
  "battery_node"
  "command_node"
  "pose_node"
  "task_manager_node"
)

foreach(NODE ${NODES})
  add_executable(${NODE} src/${NODE}.cpp)
  ament_target_dependencies(${NODE} 
    rclcpp 
    robot_interfaces 
    geometry_msgs 
    std_msgs
  )
endforeach()

install(TARGETS
  ${NODES}
  DESTINATION lib/${PROJECT_NAME}
)

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
