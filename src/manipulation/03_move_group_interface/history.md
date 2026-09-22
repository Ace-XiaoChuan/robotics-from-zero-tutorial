# 从这里学到了什么？

本文行数：408行，预期阅读时长：20分钟

```
[INFO] [launch]: All log files can be found below /home/ace/.ros/log/2026-04-09-21-10-22-150855-DESKTOP-CD3R3PF-2603
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [rviz2-1]: process started with pid [2711]
[INFO] [static_transform_publisher-2]: process started with pid [2713]
[INFO] [robot_state_publisher-3]: process started with pid [2715]
[INFO] [move_group-4]: process started with pid [2717]
[INFO] [ros2_control_node-5]: process started with pid [2719]
[INFO] [spawner-6]: process started with pid [2721]
[INFO] [spawner-7]: process started with pid [2723]
[INFO] [spawner-8]: process started with pid [2725]
[INFO] [hello_moveit-9]: process started with pid [2727]
[static_transform_publisher-2] [WARN] [1775740228.241738435] []: Old-style arguments are deprecated; see --help for new-style arguments
[static_transform_publisher-2] [INFO] [1775740229.389274706] [static_transform_publisher]: Spinning until stopped - publishing transform
[static_transform_publisher-2] translation: ('0.000000', '0.000000', '0.000000')
[static_transform_publisher-2] rotation: ('0.000000', '0.000000', '0.000000', '1.000000')
[static_transform_publisher-2] from 'world' to 'panda_link0'
[robot_state_publisher-3] [INFO] [1775740230.720263851] [robot_state_publisher]: got segment panda_hand
[robot_state_publisher-3] [INFO] [1775740230.720439419] [robot_state_publisher]: got segment panda_leftfinger
[robot_state_publisher-3] [INFO] [1775740230.720463252] [robot_state_publisher]: got segment panda_link0
[robot_state_publisher-3] [INFO] [1775740230.720472189] [robot_state_publisher]: got segment panda_link1
[robot_state_publisher-3] [INFO] [1775740230.720480829] [robot_state_publisher]: got segment panda_link2
[robot_state_publisher-3] [INFO] [1775740230.720489468] [robot_state_publisher]: got segment panda_link3
[robot_state_publisher-3] [INFO] [1775740230.720497611] [robot_state_publisher]: got segment panda_link4
[robot_state_publisher-3] [INFO] [1775740230.720506449] [robot_state_publisher]: got segment panda_link5
[robot_state_publisher-3] [INFO] [1775740230.720514492] [robot_state_publisher]: got segment panda_link6
[robot_state_publisher-3] [INFO] [1775740230.720522238] [robot_state_publisher]: got segment panda_link7
[robot_state_publisher-3] [INFO] [1775740230.720530579] [robot_state_publisher]: got segment panda_link8
[robot_state_publisher-3] [INFO] [1775740230.720539219] [robot_state_publisher]: got segment panda_rightfinger
[move_group-4] [INFO] [1775740243.273642742] [moveit_rdf_loader.rdf_loader]: Loaded robot model in 0.143799 seconds
[hello_moveit-9] [INFO] [1775740243.321843654] [moveit_rdf_loader.rdf_loader]: Loaded robot model in 0.119397 seconds
[move_group-4] [INFO] [1775740243.510298962] [moveit_robot_model.robot_model]: Loading robot model 'panda'...
[hello_moveit-9] [INFO] [1775740243.510309882] [moveit_robot_model.robot_model]: Loading robot model 'panda'...
[ros2_control_node-5] [INFO] [1775740244.021278598] [controller_manager]: Subscribing to '~/robot_description' topic for robot description file.
[ros2_control_node-5] [INFO] [1775740244.022718836] [controller_manager]: update rate is 100 Hz
[ros2_control_node-5] [INFO] [1775740244.022845257] [controller_manager]: Spawning controller_manager RT thread with scheduler priority: 50
[ros2_control_node-5] [WARN] [1775740244.023207679] [controller_manager]: No real-time kernel detected on this system. See [https://control.ros.org/master/doc/ros2_control/controller_manager/doc/userdoc.html] for details on how to enable realtime scheduling.
[ros2_control_node-5] [INFO] [1775740244.290877325] [controller_manager]: Received robot description file.
[ros2_control_node-5] [INFO] [1775740244.291187371] [resource_manager]: Loading hardware 'PandaFakeSystem' 
[ros2_control_node-5] [INFO] [1775740244.661999078] [resource_manager]: Initialize hardware 'PandaFakeSystem' 
[ros2_control_node-5] [INFO] [1775740244.662120467] [resource_manager]: Successful initialization of hardware 'PandaFakeSystem'
[ros2_control_node-5] [INFO] [1775740244.662152919] [resource_manager]: Loading hardware 'PandaHandFakeSystem' 
[ros2_control_node-5] [INFO] [1775740244.662170275] [resource_manager]: Initialize hardware 'PandaHandFakeSystem' 
[ros2_control_node-5] [INFO] [1775740244.662190199] [resource_manager]: Successful initialization of hardware 'PandaHandFakeSystem'
[ros2_control_node-5] [INFO] [1775740244.662282319] [resource_manager]: 'configure' hardware 'PandaHandFakeSystem' 
[ros2_control_node-5] [INFO] [1775740244.662311280] [resource_manager]: Successful 'configure' of hardware 'PandaHandFakeSystem'
[ros2_control_node-5] [INFO] [1775740244.662318263] [resource_manager]: 'activate' hardware 'PandaHandFakeSystem' 
[ros2_control_node-5] [INFO] [1775740244.662324220] [resource_manager]: Successful 'activate' of hardware 'PandaHandFakeSystem'
[ros2_control_node-5] [INFO] [1775740244.662328636] [resource_manager]: 'configure' hardware 'PandaFakeSystem' 
[ros2_control_node-5] [INFO] [1775740244.662333873] [resource_manager]: Successful 'configure' of hardware 'PandaFakeSystem'
[ros2_control_node-5] [INFO] [1775740244.662340241] [resource_manager]: 'activate' hardware 'PandaFakeSystem' 
[ros2_control_node-5] [INFO] [1775740244.662345786] [resource_manager]: Successful 'activate' of hardware 'PandaFakeSystem'
[move_group-4] [INFO] [1775740256.217823862] [moveit_ros.planning_scene_monitor.planning_scene_monitor]: Publishing maintained planning scene on 'monitored_planning_scene'
[move_group-4] [INFO] [1775740256.218042796] [moveit.ros_planning_interface.moveit_cpp]: Listening to 'joint_states' for joint states
[move_group-4] [INFO] [1775740256.219128273] [moveit_ros.current_state_monitor]: Listening to joint states on topic 'joint_states'
[move_group-4] [INFO] [1775740256.219712229] [moveit_ros.planning_scene_monitor.planning_scene_monitor]: Listening to '/attached_collision_object' for attached collision objects
[move_group-4] [INFO] [1775740256.219733713] [moveit_ros.planning_scene_monitor.planning_scene_monitor]: Starting planning scene monitor
[move_group-4] [INFO] [1775740256.222874030] [moveit_ros.planning_scene_monitor.planning_scene_monitor]: Listening to '/planning_scene'
[move_group-4] [INFO] [1775740256.222976652] [moveit_ros.planning_scene_monitor.planning_scene_monitor]: Starting world geometry update monitor for collision objects, attached objects, octomap updates.
[move_group-4] [INFO] [1775740256.223575498] [moveit_ros.planning_scene_monitor.planning_scene_monitor]: Listening to 'collision_object'
[move_group-4] [INFO] [1775740256.224088309] [moveit_ros.planning_scene_monitor.planning_scene_monitor]: Listening to 'planning_scene_world' for planning scene world geometry
[move_group-4] [WARN] [1775740257.564898212] [moveit.ros.occupancy_map_monitor.middleware_handle]: Resolution not specified for Octomap. Assuming resolution = 0.1 instead
[move_group-4] [ERROR] [1775740257.564969396] [moveit.ros.occupancy_map_monitor.middleware_handle]: No 3D sensor plugin(s) defined for octomap updates
[move_group-4] [INFO] [1775740257.566821167] [moveit.ros_planning_interface.moveit_cpp]: Loading planning pipeline 'ompl'
[ros2_control_node-5] [INFO] [1775740259.362990130] [controller_manager]: Loading controller 'panda_hand_controller'
[move_group-4] [INFO] [1775740260.766687270] [moveit.ros_planning.planning_pipeline]: Using planning interface 'OMPL'
[ros2_control_node-5] [INFO] [1775740260.804116456] [controller_manager]: Loading controller 'panda_arm_controller'
[spawner-8] [INFO] [1775740260.820872461] [spawner_panda_hand_controller]: Loaded panda_hand_controller
[ros2_control_node-5] [WARN] [1775740261.103452654] [panda_arm_controller]: [Deprecated]: "allow_nonzero_velocity_at_trajectory_end" is set to true. The default behavior will change to false.
[ros2_control_node-5] [INFO] [1775740261.114491429] [controller_manager]: Loading controller 'joint_state_broadcaster'
[spawner-7] [INFO] [1775740261.133677338] [spawner_panda_arm_controller]: Loaded panda_arm_controller
[ros2_control_node-5] [INFO] [1775740261.773718118] [controller_manager]: Configuring controller 'panda_hand_controller'
[ros2_control_node-5] [INFO] [1775740261.773825647] [panda_hand_controller]: Action status changes will be monitored at 20.000000 Hz.
[move_group-4] [INFO] [1775740261.774447724] [moveit_ros.add_time_optimal_parameterization]: Param 'ompl.path_tolerance' was not set. Using default value: 0.100000
[move_group-4] [INFO] [1775740261.774472814] [moveit_ros.add_time_optimal_parameterization]: Param 'ompl.resample_dt' was not set. Using default value: 0.100000
[move_group-4] [INFO] [1775740261.774480181] [moveit_ros.add_time_optimal_parameterization]: Param 'ompl.min_angle_change' was not set. Using default value: 0.001000
[move_group-4] [INFO] [1775740261.774521401] [moveit_ros.fix_workspace_bounds]: Param 'ompl.default_workspace_bounds' was not set. Using default value: 10.000000
[move_group-4] [INFO] [1775740261.774543006] [moveit_ros.fix_start_state_bounds]: Param 'ompl.start_state_max_bounds_error' was set to 0.100000
[move_group-4] [INFO] [1775740261.774550972] [moveit_ros.fix_start_state_bounds]: Param 'ompl.start_state_max_dt' was not set. Using default value: 0.500000
[move_group-4] [INFO] [1775740261.774566504] [moveit_ros.fix_start_state_collision]: Param 'ompl.start_state_max_dt' was not set. Using default value: 0.500000
[move_group-4] [INFO] [1775740261.774572378] [moveit_ros.fix_start_state_collision]: Param 'ompl.jiggle_fraction' was not set. Using default value: 0.020000
[move_group-4] [INFO] [1775740261.774592689] [moveit_ros.fix_start_state_collision]: Param 'ompl.max_sampling_attempts' was not set. Using default value: 100
[move_group-4] [INFO] [1775740261.774609615] [moveit.ros_planning.planning_pipeline]: Using planning request adapter 'Add Time Optimal Parameterization'
[move_group-4] [INFO] [1775740261.774617480] [moveit.ros_planning.planning_pipeline]: Using planning request adapter 'Resolve constraint frames to robot links'
[move_group-4] [INFO] [1775740261.774622160] [moveit.ros_planning.planning_pipeline]: Using planning request adapter 'Fix Workspace Bounds'
[move_group-4] [INFO] [1775740261.774626342] [moveit.ros_planning.planning_pipeline]: Using planning request adapter 'Fix Start State Bounds'
[move_group-4] [INFO] [1775740261.774630523] [moveit.ros_planning.planning_pipeline]: Using planning request adapter 'Fix Start State In Collision'
[move_group-4] [INFO] [1775740261.774634008] [moveit.ros_planning.planning_pipeline]: Using planning request adapter 'Fix Start State Path Constraints'
[ros2_control_node-5] [INFO] [1775740261.783800679] [controller_manager]: Configuring controller 'panda_arm_controller'
[ros2_control_node-5] [INFO] [1775740261.783961176] [panda_arm_controller]: No specific joint names are used for command interfaces. Using 'joints' parameter.
[ros2_control_node-5] [INFO] [1775740261.783992141] [panda_arm_controller]: Command interfaces are [position] and state interfaces are [position velocity].
[ros2_control_node-5] [INFO] [1775740261.784022408] [panda_arm_controller]: Using 'splines' interpolation method.
[ros2_control_node-5] [INFO] [1775740261.785979341] [panda_arm_controller]: Controller state will be published at 50.00 Hz.
[spawner-6] [INFO] [1775740261.793115899] [spawner_joint_state_broadcaster]: Loaded joint_state_broadcaster
[move_group-4] [INFO] [1775740261.815460481] [moveit.ros_planning_interface.moveit_cpp]: Loading planning pipeline 'chomp'
[ros2_control_node-5] [INFO] [1775740261.902709728] [panda_arm_controller]: Action status changes will be monitored at 20.00 Hz.
[ros2_control_node-5] [INFO] [1775740261.914403934] [controller_manager]: Configuring controller 'joint_state_broadcaster'
[ros2_control_node-5] [INFO] [1775740261.914487269] [joint_state_broadcaster]: 'joints' or 'interfaces' parameter is empty. All available state interfaces will be published
[spawner-8] [INFO] [1775740261.945209974] [spawner_panda_hand_controller]: Configured and activated panda_hand_controller
[spawner-6] [INFO] [1775740261.965646309] [spawner_joint_state_broadcaster]: Configured and activated joint_state_broadcaster
[spawner-7] [INFO] [1775740261.984566581] [spawner_panda_arm_controller]: Configured and activated panda_arm_controller
[move_group-4] [INFO] [1775740262.276991239] [moveit.ros_planning.planning_pipeline]: Using planning interface 'CHOMP'
[move_group-4] [INFO] [1775740262.279864063] [moveit_ros.add_time_optimal_parameterization]: Param 'chomp.path_tolerance' was not set. Using default value: 0.100000
[move_group-4] [INFO] [1775740262.279905264] [moveit_ros.add_time_optimal_parameterization]: Param 'chomp.resample_dt' was not set. Using default value: 0.100000
[move_group-4] [INFO] [1775740262.279911534] [moveit_ros.add_time_optimal_parameterization]: Param 'chomp.min_angle_change' was not set. Using default value: 0.001000
[move_group-4] [INFO] [1775740262.279926760] [moveit_ros.fix_workspace_bounds]: Param 'chomp.default_workspace_bounds' was not set. Using default value: 10.000000
[move_group-4] [INFO] [1775740262.279940394] [moveit_ros.fix_start_state_bounds]: Param 'chomp.start_state_max_bounds_error' was set to 0.100000
[move_group-4] [INFO] [1775740262.279944773] [moveit_ros.fix_start_state_bounds]: Param 'chomp.start_state_max_dt' was not set. Using default value: 0.500000
[move_group-4] [INFO] [1775740262.279954327] [moveit_ros.fix_start_state_collision]: Param 'chomp.start_state_max_dt' was not set. Using default value: 0.500000
[move_group-4] [INFO] [1775740262.279957810] [moveit_ros.fix_start_state_collision]: Param 'chomp.jiggle_fraction' was not set. Using default value: 0.020000
[move_group-4] [INFO] [1775740262.279961890] [moveit_ros.fix_start_state_collision]: Param 'chomp.max_sampling_attempts' was not set. Using default value: 100
[move_group-4] [INFO] [1775740262.279970648] [moveit.ros_planning.planning_pipeline]: Using planning request adapter 'Add Time Optimal Parameterization'
[move_group-4] [INFO] [1775740262.279974032] [moveit.ros_planning.planning_pipeline]: Using planning request adapter 'Fix Workspace Bounds'
[move_group-4] [INFO] [1775740262.279976619] [moveit.ros_planning.planning_pipeline]: Using planning request adapter 'Fix Start State Bounds'
[move_group-4] [INFO] [1775740262.279979008] [moveit.ros_planning.planning_pipeline]: Using planning request adapter 'Fix Start State In Collision'
[move_group-4] [INFO] [1775740262.279981396] [moveit.ros_planning.planning_pipeline]: Using planning request adapter 'Fix Start State Path Constraints'
[move_group-4] [INFO] [1775740262.282505803] [moveit.ros_planning_interface.moveit_cpp]: Loading planning pipeline 'pilz_industrial_motion_planner'
[move_group-4] [INFO] [1775740262.443871659] [moveit.pilz_industrial_motion_planner.joint_limits_aggregator]: Reading limits from namespace robot_description_planning
[move_group-4] [WARN] [1775740262.445206710] [moveit.pilz_industrial_motion_planner.joint_limits_aggregator]: Multi-DOF-Joint 'virtual_joint' not supported.
[move_group-4] [WARN] [1775740262.445275180] [moveit.pilz_industrial_motion_planner.joint_limits_aggregator]: Multi-DOF-Joint 'virtual_joint' not supported.
[move_group-4] [INFO] [1775740262.546876417] [moveit.pilz_industrial_motion_planner]: Available plugins: pilz_industrial_motion_planner/PlanningContextLoaderCIRC pilz_industrial_motion_planner/PlanningContextLoaderLIN pilz_industrial_motion_planner/PlanningContextLoaderPTP 
[move_group-4] [INFO] [1775740262.546944587] [moveit.pilz_industrial_motion_planner]: About to load: pilz_industrial_motion_planner/PlanningContextLoaderCIRC
[INFO] [spawner-7]: process has finished cleanly [pid 2723]
[INFO] [spawner-8]: process has finished cleanly [pid 2725]
[INFO] [spawner-6]: process has finished cleanly [pid 2721]
[move_group-4] [INFO] [1775740262.947592742] [moveit.pilz_industrial_motion_planner]: Registered Algorithm [CIRC]
[move_group-4] [INFO] [1775740262.947655638] [moveit.pilz_industrial_motion_planner]: About to load: pilz_industrial_motion_planner/PlanningContextLoaderLIN
[move_group-4] [INFO] [1775740263.039871243] [moveit.pilz_industrial_motion_planner]: Registered Algorithm [LIN]
[move_group-4] [INFO] [1775740263.039932623] [moveit.pilz_industrial_motion_planner]: About to load: pilz_industrial_motion_planner/PlanningContextLoaderPTP
[move_group-4] [INFO] [1775740263.043518580] [moveit.pilz_industrial_motion_planner]: Registered Algorithm [PTP]
[move_group-4] [INFO] [1775740263.043573195] [moveit.ros_planning.planning_pipeline]: Using planning interface 'Pilz Industrial Motion Planner'
[move_group-4] [INFO] [1775740263.049049671] [moveit_ros.fix_workspace_bounds]: Param 'pilz_industrial_motion_planner.default_workspace_bounds' was not set. Using default value: 10.000000
[move_group-4] [INFO] [1775740263.049109857] [moveit_ros.fix_start_state_bounds]: Param 'pilz_industrial_motion_planner.start_state_max_bounds_error' was not set. Using default value: 0.050000
[move_group-4] [INFO] [1775740263.049158104] [moveit_ros.fix_start_state_bounds]: Param 'pilz_industrial_motion_planner.start_state_max_dt' was not set. Using default value: 0.500000
[move_group-4] [INFO] [1775740263.049180985] [moveit_ros.fix_start_state_collision]: Param 'pilz_industrial_motion_planner.start_state_max_dt' was not set. Using default value: 0.500000
[move_group-4] [INFO] [1775740263.049187849] [moveit_ros.fix_start_state_collision]: Param 'pilz_industrial_motion_planner.jiggle_fraction' was not set. Using default value: 0.020000
[move_group-4] [INFO] [1775740263.049194315] [moveit_ros.fix_start_state_collision]: Param 'pilz_industrial_motion_planner.max_sampling_attempts' was not set. Using default value: 100
[move_group-4] [INFO] [1775740263.049209038] [moveit.ros_planning.planning_pipeline]: Using planning request adapter 'Fix Workspace Bounds'
[move_group-4] [INFO] [1775740263.049214709] [moveit.ros_planning.planning_pipeline]: Using planning request adapter 'Fix Start State Bounds'
[move_group-4] [INFO] [1775740263.049218190] [moveit.ros_planning.planning_pipeline]: Using planning request adapter 'Fix Start State In Collision'
[move_group-4] [INFO] [1775740263.049221374] [moveit.ros_planning.planning_pipeline]: Using planning request adapter 'Fix Start State Path Constraints'
[move_group-4] [INFO] [1775740263.168951689] [moveit.plugins.moveit_simple_controller_manager]: Added FollowJointTrajectory controller for panda_arm_controller
[move_group-4] [INFO] [1775740263.169050672] [moveit.plugins.moveit_simple_controller_manager]: Max effort set to 0.0
[move_group-4] [INFO] [1775740263.170818831] [moveit.plugins.moveit_simple_controller_manager]: Added GripperCommand controller for panda_hand_controller
[move_group-4] [INFO] [1775740263.170963972] [moveit.plugins.moveit_simple_controller_manager]: Returned 2 controllers in list
[move_group-4] [INFO] [1775740263.170999387] [moveit.plugins.moveit_simple_controller_manager]: Returned 2 controllers in list
[move_group-4] [INFO] [1775740263.171790253] [moveit_ros.trajectory_execution_manager]: Trajectory execution is managing controllers
[move_group-4] [INFO] [1775740263.171809254] [move_group.move_group]: MoveGroup debug mode is ON
[move_group-4] [INFO] [1775740263.851573189] [move_group.move_group]: 
[move_group-4] 
[move_group-4] ********************************************************
[move_group-4] * MoveGroup using: 
[move_group-4] *     - ApplyPlanningSceneService
[move_group-4] *     - ClearOctomapService
[move_group-4] *     - CartesianPathService
[move_group-4] *     - ExecuteTrajectoryAction
[move_group-4] *     - GetPlanningSceneService
[move_group-4] *     - KinematicsService
[move_group-4] *     - MoveAction
[move_group-4] *     - MotionPlanService
[move_group-4] *     - QueryPlannersService
[move_group-4] *     - StateValidationService
[move_group-4] ********************************************************
[move_group-4] 
[move_group-4] [INFO] [1775740263.851619248] [moveit_move_group_capabilities_base.move_group_context]: MoveGroup context using planning plugin ompl_interface/OMPLPlanner
[move_group-4] [INFO] [1775740263.851625814] [moveit_move_group_capabilities_base.move_group_context]: MoveGroup context initialization complete
[move_group-4] Loading 'move_group/ApplyPlanningSceneService'...
[move_group-4] Loading 'move_group/ClearOctomapService'...
[move_group-4] Loading 'move_group/MoveGroupCartesianPathService'...
[move_group-4] Loading 'move_group/MoveGroupExecuteTrajectoryAction'...
[move_group-4] Loading 'move_group/MoveGroupGetPlanningSceneService'...
[move_group-4] Loading 'move_group/MoveGroupKinematicsService'...
[move_group-4] Loading 'move_group/MoveGroupMoveAction'...
[move_group-4] Loading 'move_group/MoveGroupPlanService'...
[move_group-4] Loading 'move_group/MoveGroupQueryPlannersService'...
[move_group-4] Loading 'move_group/MoveGroupStateValidationService'...
[move_group-4] 
[move_group-4] You can start planning now!
[move_group-4] 
[hello_moveit-9] [INFO] [1775740263.852701094] [move_group_interface]: Ready to take commands for planning group panda_arm.
[hello_moveit-9] [INFO] [1775740263.852850513] [move_group_interface]: MoveGroup action client/server ready
[move_group-4] [INFO] [1775740263.854539585] [moveit_move_group_default_capabilities.move_action_capability]: Received request
[move_group-4] [INFO] [1775740263.854736456] [moveit_move_group_default_capabilities.move_action_capability]: executing..
[hello_moveit-9] [INFO] [1775740263.854886671] [move_group_interface]: Planning request accepted
[move_group-4] [INFO] [1775740263.863883349] [moveit_move_group_default_capabilities.move_action_capability]: Planning request received for MoveGroup action. Forwarding to planning pipeline.
[move_group-4] [INFO] [1775740264.352588047] [moveit.ompl_planning.model_based_planning_context]: Planner configuration 'panda_arm' will use planner 'geometric::RRTConnect'. Additional configuration parameters will be set when the planner is constructed.
[move_group-4] [INFO] [1775740265.249773080] [moveit_move_group_default_capabilities.move_action_capability]: Motion plan was computed successfully.
[hello_moveit-9] [INFO] [1775740265.250899758] [move_group_interface]: Planning request complete!
[hello_moveit-9] [INFO] [1775740265.251096800] [move_group_interface]: time taken to generate plan: 0.350913 seconds
[move_group-4] [INFO] [1775740265.252020272] [moveit_move_group_default_capabilities.execute_trajectory_action_capability]: Received goal request
[move_group-4] [INFO] [1775740265.252149612] [moveit_move_group_default_capabilities.execute_trajectory_action_capability]: Execution request received
[move_group-4] [INFO] [1775740265.252175559] [moveit.plugins.moveit_simple_controller_manager]: Returned 2 controllers in list
[move_group-4] [INFO] [1775740265.252190173] [moveit.plugins.moveit_simple_controller_manager]: Returned 2 controllers in list
[move_group-4] [INFO] [1775740265.252384829] [moveit_ros.trajectory_execution_manager]: Validating trajectory with allowed_start_tolerance 0.01
[hello_moveit-9] [INFO] [1775740265.252542801] [move_group_interface]: Execute request accepted
[move_group-4] [INFO] [1775740265.253937106] [moveit_ros.trajectory_execution_manager]: Starting trajectory execution ...
[move_group-4] [INFO] [1775740265.254013258] [moveit.plugins.moveit_simple_controller_manager]: Returned 2 controllers in list
[move_group-4] [INFO] [1775740265.254041790] [moveit.plugins.moveit_simple_controller_manager]: Returned 2 controllers in list
[move_group-4] [INFO] [1775740265.254284961] [moveit.simple_controller_manager.follow_joint_trajectory_controller_handle]: sending trajectory to panda_arm_controller
[ros2_control_node-5] [INFO] [1775740265.255939636] [panda_arm_controller]: Received new action goal
[ros2_control_node-5] [INFO] [1775740265.256013203] [panda_arm_controller]: Accepted new action goal
[move_group-4] [INFO] [1775740265.256370503] [moveit.simple_controller_manager.follow_joint_trajectory_controller_handle]: panda_arm_controller started execution
[move_group-4] [INFO] [1775740265.256390188] [moveit.simple_controller_manager.follow_joint_trajectory_controller_handle]: Goal request accepted!
[ros2_control_node-5] [INFO] [1775740275.693388529] [panda_arm_controller]: Goal reached, success!
[move_group-4] [INFO] [1775740275.734926558] [moveit.simple_controller_manager.follow_joint_trajectory_controller_handle]: Controller 'panda_arm_controller' successfully finished
[move_group-4] [INFO] [1775740275.763671453] [moveit_ros.trajectory_execution_manager]: Completed trajectory execution with status SUCCEEDED ...
[move_group-4] [INFO] [1775740275.763911775] [moveit_move_group_default_capabilities.execute_trajectory_action_capability]: Execution completed: SUCCEEDED
[hello_moveit-9] [INFO] [1775740275.764279057] [move_group_interface]: Execute request success!
[INFO] [hello_moveit-9]: process has finished cleanly [pid 2727]
[rviz2-1] [INFO] [1775740298.768154740] [rviz2]: Stereo is NOT SUPPORTED
[rviz2-1] [INFO] [1775740298.768390312] [rviz2]: OpenGl version: 4.5 (GLSL 4.5)
[rviz2-1] [INFO] [1775740300.378980038] [rviz2]: Stereo is NOT SUPPORTED
[rviz2-1] [INFO] [1775740302.107697440] [moveit_rdf_loader.rdf_loader]: Loaded robot model in 0.15672 seconds
[rviz2-1] [INFO] [1775740302.107858479] [moveit_robot_model.robot_model]: Loading robot model 'panda'...
[rviz2-1] [INFO] [1775740304.520068545] [moveit_rdf_loader.rdf_loader]: Loaded robot model in 0.00235595 seconds
[rviz2-1] [INFO] [1775740304.520145968] [moveit_robot_model.robot_model]: Loading robot model 'panda'...
[rviz2-1] [INFO] [1775740304.718006174] [moveit_ros.planning_scene_monitor.planning_scene_monitor]: Starting planning scene monitor
[rviz2-1] [INFO] [1775740304.719782739] [moveit_ros.planning_scene_monitor.planning_scene_monitor]: Listening to '/monitored_planning_scene'
```

## 什么是ros2_control？

`ros2_control` 是 ROS 2 生态系统中**最核心、最重要的组件之一**。如果你想让你的机器人动起来（无论是真实的硬件，还是在 Gazebo 等仿真软件中），你几乎都会用到它。

简单来说，`ros2_control` 是一个用于**机器人控制的通用框架**。它充当了高级算法（如 Navigation2 导航、MoveIt2 机械臂规划）和底层物理硬件（电机、编码器）之间的**桥梁**。

下面我将从它的架构、工作原理、核心概念以及为什么使用它这四个方面为你通俗地讲解。

---

### 一、 核心架构（它是如何构成的？）

`ros2_control` 的架构非常优雅，主要分为三层：**控制器管理器（Controller Manager）**、**控制器（Controllers）** 和 **硬件接口（Hardware Interfaces）**。

#### 1. Controller Manager (CM - 控制器管理器)
这是 `ros2_control` 的“大管家”。
*   **作用**：它负责管理所有的控制器和硬件接口。它决定什么时候加载控制器、什么时候启动/停止它们。
*   **控制循环**：它内部运行着一个高频的实时控制循环（Update Loop）。在这个循环里，它负责从硬件读取数据，把数据交给控制器计算，再把控制器的计算结果写入硬件。

#### 2. Controllers (控制器)
这是“大脑的运动皮层”，负责具体的控制算法。
*   **作用**：它们订阅 ROS 2 的话题（比如 `/cmd_vel` 速度指令，或者机械臂的轨迹指令），然后将其转化为具体的关节命令（如某个电机应该转多快、输出多大扭矩）。
*   **复用性**：官方提供了一个叫 `ros2_controllers` 的包，里面包含了很多写好的标准控制器，你直接拿来用就行，不用自己造轮子。例如：
    *   `diff_drive_controller`：用于两轮差速小车。
    *   `joint_trajectory_controller`：用于机械臂执行轨迹。
    *   `joint_state_broadcaster`：专门用于读取所有关节状态并发布到 `/joint_states` 话题（严格来说它只是个广播器，但也算作Controller）。

#### 3. Hardware Interfaces (硬件接口 / 硬件抽象层)
这是“神经末梢和肌肉”，负责和真实的物理世界（或仿真器）打交道。
*   **作用**：这是你需要针对你的特定硬件编写（或配置）代码的地方。它可能通过串口、CAN总线、EtherCAT 等协议与真实的电机驱动器通信。
*   **分类**：
    *   **System**：复杂的系统（如整个机械臂或整个移动底盘）。
    *   **Sensor**：只读传感器（如 IMU、力矩传感器）。
    *   **Actuator**：单一的执行器（如单个电机）。
*   **接口类型**：它定义了两种数据通道：
    *   **State Interfaces (状态接口)**：只能读，比如当前的角度、速度、电流。
    *   **Command Interfaces (命令接口)**：只能写，比如目标角度、目标速度。

---

### 二、 工作原理（数据是如何流动的？）

`ros2_control` 的核心是一个周期性的实时循环（通常频率在 100Hz 到 1000Hz 以上）。在一个周期内，发生以下三步：

1.  **Read（读）**：Controller Manager 调用硬件接口的 `read()` 函数。硬件接口通过总线去读取真实电机的编码器数据，并更新到共享内存中（状态接口）。
2.  **Update（更新）**：Controller Manager 调用所有激活的 Controller 的 `update()` 函数。Controller 根据刚才读到的状态数据，以及上层发来的 ROS 指令，运行 PID 等算法，计算出下一步应该输出的值，写入到共享内存中（命令接口）。
3.  **Write（写）**：Controller Manager 调用硬件接口的 `write()` 函数。硬件接口把共享内存里的命令数据，打包通过总线发送给真实的电机驱动器。

*整个过程完全在内存中进行，不经过 ROS 2 的 DDS 网络通信，因此可以保证极高的实时性（Real-time）。*

---

### 三、 如何配置？ (URDF 与 YAML)

要使用 `ros2_control`，你通常需要修改两个文件：

**1. URDF 文件 (在机器人的模型描述中加入硬件信息)**
你需要告诉 `ros2_control` 你的机器人有什么关节，支持什么命令和状态。
```xml
<ros2_control name="MyRobotHardware" type="system">
  <!-- 指定使用哪个硬件接口代码（比如真实的串口通信，或者Gazebo仿真接口） -->
  <hardware>
    <plugin>my_robot_driver/MyRobotHardwareInterface</plugin>
  </hardware>
  
  <!-- 定义一个叫 joint1 的关节 -->
  <joint name="joint1">
    <command_interface name="velocity"/> <!-- 我可以向它发送速度命令 -->
    <state_interface name="position"/>   <!-- 我可以读取它的当前位置 -->
    <state_interface name="velocity"/>   <!-- 我可以读取它的当前速度 -->
  </joint>
</ros2_control>
```

**2. YAML 配置文件**
告诉 Controller Manager 要加载哪些控制器，以及它们的参数。
```yaml
controller_manager:
  ros__parameters:
    update_rate: 100  # 控制循环频率 100Hz
    
    joint_state_broadcaster:
      type: joint_state_broadcaster/JointStateBroadcaster
      
    my_velocity_controller:
      type: velocity_controllers/JointGroupVelocityController
```

---

### 四、 为什么要用 `ros2_control`？

很多初学者会问：**“我直接写个 ROS 2 节点，订阅 `/cmd_vel`，然后通过串口把数据发给电机不就行了吗？为什么要搞这么复杂？”**

确实可以，但 `ros2_control` 解决了以下关键问题：

1.  **无缝切换仿真与真机 (Sim-to-Real)**：
    这是最大的优势。因为 `ros2_control` 做了硬件抽象，你只需要在 URDF 里把 `<plugin>` 从 `gazebo_ros2_control` 换成你写的真机驱动插件，**上层的所有算法（导航、控制参数）一行代码都不用改**。
2.  **保证实时性 (Real-Time Performance)**：
    ROS 2 的话题（Topics）通信有延迟和不确定性。如果用普通节点跑 PID 控制器，可能因为网络波动导致机器人抽搐。`ros2_control` 将控制器和硬件接口放在同一个进程的共享内存里，保证了严格的实时控制。
3.  **标准化与复用**：
    你不需要自己去写差速运动学解算、阿克曼转向解算、机械臂样条插值算法。官方的 `ros2_controllers` 已经写好了世界上最久经考验的算法，直接配置即可。
4.  **生命周期与冲突管理**：
    假设你有一个机械臂，你想一会儿用“位置模式”控制它，一会儿用“力矩模式”控制它。`ros2_control` 的管理器允许你动态地停止（Stop）位置控制器，并启动（Start）力矩控制器，同时保证两个控制器不会同时向电机发送冲突的命令。

### 总结

可以将 `ros2_control` 想象成机器人的**脊髓**：
*   你的电脑（或者树莓派）上的导航算法是**大脑**，负责思考去哪里。
*   `ros2_control` 的控制器是**脊髓**，把大脑的高级指令翻译成肌肉电信号。
*   `ros2_control` 的硬件接口是**神经末梢**，直接连接着机器人的**肌肉（电机）**。

掌握了 `ros2_control`，你就真正掌握了将复杂的 AI 和规划算法落地到物理机器人上的钥匙。

---

## move_group

在 ROS 和 MoveIt 的生态中，理解 `move_group` 以及它与你自己写的代码之间的关系，是掌握机械臂控制的关键。

我们可以用一个生动的比喻来理解：**你自己写的节点是“发号施令的老板”，而 `move_group` 是“精通业务的专业司机（或大脑中枢）”，机械臂硬件则是“车”。**

下面我为你详细拆解这两部分。

---

### 一、 什么是 `move_group`？

`move_group` 是 MoveIt 框架中**最核心的 ROS 节点（Node）**。你可以把它看作是控制机械臂的“大脑”或“中央处理器”。

当你运行 MoveIt Setup Assistant 生成配置包后，启动的那个主节点通常就是 `move_group`。它的主要职责是将各种复杂的机器人学计算整合在一起：

1. **运动学求解（Kinematics）：** 包含正运动学（FK）和逆运动学（IK）。比如你告诉它“我要末端抓手到达空间中(X, Y, Z)的位置”，`move_group` 会计算出机械臂的各个关节需要转动多少度才能到达那里。
2. **路径规划（Path Planning）：** 调用底层的规划算法库（如 OMPL、Pilz 等），在起点和终点之间计算出一条平滑的轨迹。
3. **碰撞检测（Collision Checking）：** 结合机器人自身的 3D 模型（URDF）和外部环境（通过摄像头获取的点云或你在代码中添加的障碍物），确保规划出的轨迹不会让机械臂撞到自己或周围的桌子、墙壁。
4. **状态维护（Planning Scene）：** 它时刻监听着机器人的当前关节状态（`joint_states`）和坐标变换（`tf`），知道机械臂现在处于什么姿态。
5. **轨迹执行（Execution）：** 规划好路径后，`move_group` 会将这一连串的关节角度指令发送给底层的机器人控制器（通常通过 `FollowJointTrajectory` Action）。

**总结来说：`move_group` 是一个“黑盒服务站”，它集成了所有复杂的数学计算和物理防碰撞逻辑。**

---

### 二、 `move_group` 和你自己写的节点有什么关系？

你自己写的节点（通常是用 C++ 或 Python 写的业务逻辑代码），与 `move_group` 之间是**客户端（Client）与服务端（Server）的关系**。

#### 1. 明确的分工
* **你的节点（老板/指挥官）：** 负责**高层逻辑**。比如：“如果摄像头看到了红色方块，就去抓取它，然后放到左边的篮子里。”你不需要知道机械臂的具体关节角度怎么变，也不需要自己写避障算法。
* **`move_group` 节点（专业司机）：** 负责**底层执行**。它接收你节点发来的高层指令，计算出具体的关节转动轨迹，避开障碍物，然后驱动电机。

#### 2. 它们是如何通信的？
由于你的节点和 `move_group` 是两个独立的 ROS 节点，它们之间需要通过 ROS 的通信机制（Topic, Service, Action）来交流。
为了让你写代码更简单，MoveIt 提供了封装好的 **API 接口**：
* **C++:** `moveit::planning_interface::MoveGroupInterface`
* **Python:** `moveit_commander.MoveGroupCommander`

当你实例化这些接口时，**你的节点本质上变成了一个 Action Client（动作客户端），而 `move_group` 就是一个 Action Server（动作服务端）。**

#### 3. 典型的交互流程（以抓取一个杯子为例）

假设你写了一个 Python 节点来控制机械臂去抓杯子，真实的底层交互是这样的：

1. **你的节点设定目标：**
   你在代码中写 `group.set_pose_target(cup_pose)`，然后调用 `group.go()`。
2. **你的节点发送请求（Request）：**
   `go()` 函数会在底层打包一个请求，通过 ROS Action 发送给正在后台运行的 `move_group` 节点。请求内容大约是：“我想让末端到达这个位姿，请帮我规划并执行。”
3. **`move_group` 开始工作：**
   `move_group` 收到请求后，开始算逆运动学，开始做碰撞检测，开始用 OMPL 规划路径。
4. **`move_group` 控制机械臂：**
   `move_group` 规划成功后，它会把生成的时间-位置轨迹发送给真正的机械臂控制器驱动硬件。
5. **`move_group` 返回结果（Response）：**
   机械臂到达位置后，`move_group` 会通过 Action 的反馈机制告诉你的节点：“老板，任务完成了（Success）！”或者“报告老板，规划失败，因为有个障碍物挡住了（Failed）。”
6. **你的节点继续往下走：**
   你的代码收到 `go()` 返回的成功状态，接着执行下一步控制夹爪闭合的代码。

### 三、 常见误区与总结

* **误区1：以为自己写的代码就是控制机械臂的全部。**
  * **真相：** 你的代码非常轻量，它只是一个“调用者”。如果没有启动 `move_group` 节点，你的代码一运行就会卡死或者报错（通常提示连不上 action server）。
* **误区2：以为规划算法是在自己的代码里跑的。**
  * **真相：** 你的代码里调用 `plan()` 或 `go()` 时，计算过程实际上发生在 `move_group` 这个独立进程的内存里。

**一句话总结：**
**你自己写的节点是业务的大脑（决定“做什么”），`move_group` 是运动控制的大脑（决定“怎么安全地做”）。你通过 MoveIt 提供的 API，跨节点指挥 `move_group` 帮你完成复杂的机械臂运动。**
