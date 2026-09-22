"""ROS graph integration checks, not reader exercises. Uses an isolated namespace per test."""
import math
import os
from pathlib import Path
import signal
import subprocess
import time
import uuid

# Keep the test graph on this machine; no hardware or existing robot topics are used.
os.environ['ROS_LOCALHOST_ONLY'] = '1'
os.environ.setdefault('ROS_DOMAIN_ID', '97')
os.environ['ROS_LOG_DIR'] = '/tmp/lesson1_ros_test_logs'

import pytest
import rclpy
from action_msgs.msg import GoalStatus
from ament_index_python.packages import get_package_prefix
from geometry_msgs.msg import PointStamped, Twist
from rclpy.action import ActionClient
from robot_interfaces.action import Navigation
from robot_interfaces.srv import GetRobotStatus
from std_msgs.msg import Int32


class Graph:
    def __init__(self, directory):
        self.directory = directory
        self.namespace = '/lesson1_test_' + uuid.uuid4().hex[:10]
        self.node = rclpy.create_node('observer', namespace=self.namespace)
        self.processes = []
        self.feedback = []
        self.pose = None
        self.velocity = None
        self.synthetic = False
        self.publish_pose = self.publish_battery = True
        self.level = 100
        self.frame = 'map'
        self.stamp_offset = 0.0
        self.x = 0.0
        self.pose_pub = self.node.create_publisher(PointStamped, 'robot_pose', 10)
        self.battery_pub = self.node.create_publisher(Int32, 'battery_level', 10)
        self.command_pub = self.node.create_publisher(Twist, 'cmd_vel', 1)
        self.node.create_subscription(PointStamped, 'robot_pose', self.on_pose, 10)
        self.node.create_subscription(Twist, 'cmd_vel', self.on_velocity, 10)
        self.node.create_timer(0.05, self.feed)
        self.action = ActionClient(self.node, Navigation, 'navigation')
        self.status = self.node.create_client(GetRobotStatus, 'get_robot_status')

    def on_pose(self, msg):
        self.pose = msg

    def on_velocity(self, msg):
        self.velocity = msg

    def feed(self):
        if not self.synthetic:
            return
        if self.publish_battery:
            self.battery_pub.publish(Int32(data=self.level))
        if self.publish_pose:
            msg = PointStamped()
            msg.header.frame_id = self.frame
            msg.header.stamp = (self.node.get_clock().now() +
                rclpy.duration.Duration(seconds=self.stamp_offset)).to_msg()
            msg.point.x = self.x
            self.pose_pub.publish(msg)

    def process(self, args, name):
        path = self.directory / (name + '.log')
        stream = path.open('w')
        process = subprocess.Popen(args, stdout=stream, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        self.processes.append((process, stream, path))
        return process, path

    def start(self, name, **parameters):
        executable = Path(get_package_prefix('ros2_comm_demo')) / 'lib/ros2_comm_demo' / name
        args = [str(executable), '--ros-args', '-r', '__ns:=' + self.namespace]
        for key, value in parameters.items():
            args += ['-p', f'{key}:={value}']
        return self.process(args, name)

    def wait(self, predicate, seconds=6.0):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.02)
            if predicate():
                return
        logs = '\n'.join(p.read_text()[-3000:] for _, _, p in self.processes)
        pytest.fail('Timed out waiting for ROS condition\n' + logs)

    def pump(self, seconds):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.02)

    def resolve(self, future, seconds=6.0):
        self.wait(future.done, seconds)
        return future.result()

    def query(self):
        self.wait(self.status.service_is_ready)
        return self.resolve(self.status.call_async(GetRobotStatus.Request()))

    def ready(self):
        self.wait(self.action.server_is_ready)
        deadline = time.monotonic() + 6
        while time.monotonic() < deadline:
            if self.query().valid:
                return
            self.pump(0.05)
        pytest.fail('state never became valid')

    def goal(self, x=1.0, y=0.5):
        self.wait(self.action.server_is_ready)
        return self.resolve(self.action.send_goal_async(
            Navigation.Goal(target_x=float(x), target_y=float(y)),
            feedback_callback=lambda msg: self.feedback.append(msg.feedback)))

    def stop(self, process):
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)

    def close(self):
        for process, stream, _ in reversed(self.processes):
            self.stop(process)
            stream.close()
        self.action.destroy()
        self.node.destroy_node()


@pytest.fixture
def graph(tmp_path):
    rclpy.init()
    instance = Graph(tmp_path)
    try:
        yield instance
    finally:
        instance.close()
        rclpy.shutdown()


def test_launch_default_client_reaches_target(graph):
    _, log = graph.process(['ros2', 'launch', 'ros2_comm_demo', 'launch.py',
                           'namespace:=' + graph.namespace.lstrip('/')], 'launch')
    graph.wait(lambda: 'message=arrived' in log.read_text(), 18)
    state = graph.query()
    error = math.hypot(state.pose.point.x - 1.0, state.pose.point.y - 0.5)
    assert state.valid and not state.has_task and error <= 0.035
    assert state.pose.header.frame_id == 'map'
    graph.pump(0.5)
    after = graph.query()
    assert math.hypot(after.pose.point.x-state.pose.point.x,
                      after.pose.point.y-state.pose.point.y) < 0.015
    print(f'default target error: {error:.6f} m')


def test_cancel_reject_busy_and_accept_next_goal(graph):
    graph.start('battery_node')
    graph.start('pose_node')
    graph.start('task_manager_node')
    graph.ready()
    goal = graph.goal(3, 2)
    assert goal.accepted
    graph.wait(lambda: len(graph.feedback) >= 2)
    assert graph.query().has_task
    assert not graph.goal(1, 0).accepted
    assert graph.resolve(goal.cancel_goal_async()).goals_canceling
    result = graph.resolve(goal.get_result_async())
    assert result.status == GoalStatus.STATUS_CANCELED
    assert not result.result.success and result.result.message == 'canceled'
    graph.wait(lambda: graph.velocity is not None and graph.velocity.linear.x == 0)
    graph.pump(0.15)
    state = graph.query()
    assert not state.has_task
    next_goal = graph.goal(state.pose.point.x, state.pose.point.y)
    assert next_goal.accepted
    assert graph.resolve(next_goal.get_result_async()).status == GoalStatus.STATUS_SUCCEEDED


@pytest.mark.parametrize('case', ['no_state', 'nan_goal', 'out_of_bounds', 'low_battery',
                                  'wrong_frame', 'old_stamp', 'future_stamp', 'nan_pose'])
def test_reject_invalid_inputs(graph, case):
    graph.synthetic = case != 'no_state'
    if case == 'low_battery': graph.level = 10
    if case == 'wrong_frame': graph.frame = 'camera'
    if case == 'old_stamp': graph.stamp_offset = -10.0
    if case == 'future_stamp': graph.stamp_offset = 10.0
    if case == 'nan_pose': graph.x = float('nan')
    graph.start('task_manager_node')
    graph.wait(graph.action.server_is_ready)
    graph.pump(0.4)
    goal = graph.goal(float('nan') if case == 'nan_goal' else
                      6.0 if case == 'out_of_bounds' else 1.0, 0)
    assert not goal.accepted
    assert not graph.query().has_task


@pytest.mark.parametrize('case, reason', [('stale_pose', 'state missing or stale'),
                                        ('stale_battery', 'state missing or stale'),
                                        ('low_battery', 'low battery'),
                                        ('timeout', 'task timeout')])
def test_abort_and_stop(graph, case, reason):
    graph.synthetic = True
    graph.start('task_manager_node', state_timeout_s=0.35,
                task_timeout_s=0.8 if case == 'timeout' else 5.0)
    graph.ready()
    goal = graph.goal(2, 1)
    assert goal.accepted
    graph.wait(lambda: len(graph.feedback) > 0)
    if case == 'stale_pose': graph.publish_pose = False
    if case == 'stale_battery': graph.publish_battery = False
    if case == 'low_battery': graph.level = 1
    result = graph.resolve(goal.get_result_async())
    assert result.status == GoalStatus.STATUS_ABORTED
    assert result.result.message == reason and not result.result.success
    graph.wait(lambda: graph.velocity is not None and graph.velocity.linear.x == 0
               and graph.velocity.linear.y == 0)
    assert not graph.query().has_task


def test_client_waits_for_late_server(graph):
    _, log = graph.start('command_node', target_x=0.2, target_y=0.1)
    graph.pump(0.8)
    graph.start('battery_node')
    graph.start('pose_node')
    graph.start('task_manager_node')
    graph.wait(lambda: 'message=arrived' in log.read_text(), 12)


def test_pose_stops_when_commands_disappear(graph):
    graph.start('pose_node', command_timeout_s=0.2)
    graph.wait(lambda: graph.command_pub.get_subscription_count() > 0)
    command = Twist()
    command.linear.x = 5.0  # The simulator must cap this to 0.5 m/s.
    # Subscription count can become non-zero just before the DDS data path is
    # ready. Publish briefly, as a real velocity controller would.
    deadline = time.monotonic() + 0.15
    while time.monotonic() < deadline:
        graph.command_pub.publish(command)
        graph.pump(0.02)
    graph.pump(0.45)
    first = graph.pose.point.x
    # 0.15 s command stream plus at most the 0.2 s watchdog at 0.5 m/s.
    assert 0.02 < first <= 0.19
    graph.pump(0.4)
    assert abs(graph.pose.point.x - first) < 0.001


def test_client_result_timeout_does_not_resend(graph):
    graph.synthetic = True
    graph.start('task_manager_node', task_timeout_s=10.0)
    _, log = graph.start('command_node', result_timeout_s=0.6)
    graph.wait(lambda: 'Result timeout' in log.read_text())
    graph.wait(lambda: 'message=canceled' in log.read_text())
    assert not graph.query().has_task
    graph.pump(0.5)
    assert log.read_text().count('Goal accepted') == 1
