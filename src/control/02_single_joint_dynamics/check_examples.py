"""核对第二章的瞬时力矩计算；不积分、不运行控制闭环。"""

from dataclasses import dataclass
import math
import unittest


@dataclass(frozen=True)
class Rod:
    mass: float = 2.0          # kg，均匀杆
    length: float = 0.6        # m，转轴到杆端
    damping: float = 0.2       # N*m*s/rad
    gravity: float = 9.81      # m/s^2，世界 -y 方向
    payload: float = 0.0       # kg，刚性固定在杆端的质点

    @property
    def inertia(self):
        return self.mass * self.length**2 / 3 + self.payload * self.length**2

    @property
    def gravity_coefficient(self):
        return self.gravity * (self.mass * self.length / 2 + self.payload * self.length)

    def acceleration(self, q, velocity, motor, external=0.0):
        """q: rad；velocity: rad/s；motor/external: 关节实际力矩 N*m。"""
        net = motor + external - self.damping * velocity - self.gravity_coefficient * math.sin(q)
        return net / self.inertia

    def required_motor(self, q, velocity, acceleration, external=0.0):
        """计算需求，不自动限幅；返回 N*m。"""
        return (self.inertia * acceleration + self.damping * velocity
                + self.gravity_coefficient * math.sin(q) - external)


class ChapterExamples(unittest.TestCase):
    def setUp(self):
        self.rod = Rod()
        self.q = math.pi / 6

    def test_release_and_hold(self):
        self.assertAlmostEqual(self.rod.acceleration(self.q, 0, 0), -12.2625)
        for q, hold in [(0, 0), (self.q, 2.943), (math.pi / 2, 5.886)]:
            with self.subTest(q=q):
                self.assertAlmostEqual(self.rod.required_motor(q, 0, 0), hold)
                self.assertAlmostEqual(self.rod.acceleration(q, 0, hold), 0)

    def test_velocity_changes_motion_at_same_angle(self):
        # 表中的独立手算结果；正加速度也可以意味着对负速度减速。
        cases = [(0, 2.943, 0), (1, 2.943, -5 / 6), (-1, 2.943, 5 / 6),
                 (1, 3.143, 0), (1, 3.623, 2), (1, 2, -4.7625),
                 (-1, 3.5, 3.1541666666666667)]
        for velocity, motor, expected in cases:
            with self.subTest(velocity=velocity, motor=motor):
                self.assertAlmostEqual(self.rod.acceleration(self.q, velocity, motor), expected)

    def test_inverse_calculation_and_round_trip(self):
        self.assertAlmostEqual(self.rod.required_motor(self.q, 1, 2), 3.623)
        for q, velocity, desired, external in [(0, 0, 0, 0), (.4, -2, 3, -.5),
                                               (-.7, 1, -2, .3)]:
            motor = self.rod.required_motor(q, velocity, desired, external)
            self.assertAlmostEqual(self.rod.acceleration(q, velocity, motor, external), desired)

    def test_payload_changes_both_gravity_and_inertia(self):
        loaded = Rod(payload=1)
        self.assertAlmostEqual(loaded.inertia, .60)
        self.assertAlmostEqual(loaded.gravity_coefficient, 11.772)
        self.assertAlmostEqual(loaded.required_motor(self.q, 1, 2), 7.286)
        self.assertAlmostEqual(loaded.acceleration(self.q, 1, 3.623), -4.105)
        # 惯量独立核对：均匀质量分段位于各段中点，另加端点质点。
        segments = 10000
        discrete = sum((loaded.mass / segments) *
                       (loaded.length * (i + .5) / segments)**2
                       for i in range(segments))
        discrete += loaded.payload * loaded.length**2
        self.assertAlmostEqual(discrete, loaded.inertia, delta=1e-8)

    def test_torque_limit_and_static_boundary(self):
        limit = 4.0
        self.assertAlmostEqual(self.rod.acceleration(math.pi / 2, 0, limit), -7.858333333333333)
        boundary = math.asin(limit / self.rod.gravity_coefficient)
        self.assertAlmostEqual(boundary, .7471881398150662)
        self.assertAlmostEqual(math.degrees(boundary), 42.810726913634156)
        self.assertAlmostEqual(self.rod.acceleration(boundary, 0, limit), 0)
        self.assertLess(self.rod.required_motor(boundary - .01, 0, 0), limit)
        self.assertGreater(self.rod.required_motor(boundary + .01, 0, 0), limit)

    def test_external_torque(self):
        self.assertAlmostEqual(self.rod.acceleration(self.q, 0, 2.943, .48), 2)
        required = self.rod.required_motor(self.q, 0, 0, .48)
        self.assertAlmostEqual(required, 2.463)
        self.assertAlmostEqual(self.rod.acceleration(self.q, 0, required, .48), 0)

    def test_gravity_direction_from_force_geometry(self):
        # r=(l_c*sin(q), -l_c*cos(q)); F=(0, -m*g)；叉乘 z 分量。
        for q in [-math.pi / 2, -.3, 0, self.q, math.pi / 2]:
            x = self.rod.length / 2 * math.sin(q)
            y = -self.rod.length / 2 * math.cos(q)
            force_x, force_y = 0, -self.rod.mass * self.rod.gravity
            torque = x * force_y - y * force_x
            self.assertAlmostEqual(self.rod.acceleration(q, 0, 0) * self.rod.inertia, torque)
            if 0 < q < math.pi:
                self.assertLess(torque, 0)
            elif -math.pi < q < 0:
                self.assertGreater(torque, 0)

    def test_direction_symmetry_and_damping(self):
        for q, velocity, motor, external in [(.3, 1, 2, -.2), (-.6, -2, -.5, .4)]:
            self.assertAlmostEqual(self.rod.acceleration(-q, -velocity, -motor, -external),
                                   -self.rod.acceleration(q, velocity, motor, external))
        for velocity in [-3, -1, 0, 1, 3]:
            damping_torque = -self.rod.damping * velocity
            self.assertLessEqual(damping_torque * velocity, 0)  # 耗散功率不得为正。


if __name__ == '__main__':
    unittest.main(verbosity=2)
