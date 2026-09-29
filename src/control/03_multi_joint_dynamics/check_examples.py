"""第三章两根均匀细杆的瞬时动力学核对；不积分、不模拟控制。"""

import math
import unittest

# 世界 x 向右、y 向上；关节 +z 朝读者。q2 是相对肘角。
# q: rad，速度: rad/s，力矩: N*m，惯量: kg*m^2。
M1 = M2 = 2.0
L1 = L2 = 0.6
LC1 = LC2 = 0.3
IC1 = IC2 = 0.06  # 绕各杆自身质心，不能代入绕端点的惯量。
G = 9.81
DAMPING = (0.2, 0.2)


def matvec(matrix, vector):
    return [sum(a * b for a, b in zip(row, vector)) for row in matrix]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def mass_matrix(q):
    c = math.cos(q[1])
    m11 = IC1 + M1 * LC1**2 + IC2 + M2 * (L1**2 + LC2**2 + 2 * L1 * LC2 * c)
    m12 = IC2 + M2 * (LC2**2 + L1 * LC2 * c)
    m22 = IC2 + M2 * LC2**2
    return [[m11, m12], [m12, m22]]


def velocity_terms(q, velocity):
    h = M2 * L1 * LC2 * math.sin(q[1])
    v1, v2 = velocity
    return [-h * (2 * v1 * v2 + v2**2), h * v1**2]


def gravity_compensation(q):
    distal = M2 * LC2 * math.sin(q[0] + q[1])
    return [G * ((M1 * LC1 + M2 * L1) * math.sin(q[0]) + distal), G * distal]


def required_motor(q, velocity, acceleration, external=(0.0, 0.0)):
    inertia = matvec(mass_matrix(q), acceleration)
    c, gravity = velocity_terms(q, velocity), gravity_compensation(q)
    return [inertia[i] + c[i] + gravity[i] + DAMPING[i] * velocity[i] - external[i]
            for i in range(2)]


def forward(q, velocity, motor, external=(0.0, 0.0)):
    c, gravity = velocity_terms(q, velocity), gravity_compensation(q)
    rhs = [motor[i] + external[i] - c[i] - gravity[i] - DAMPING[i] * velocity[i]
           for i in range(2)]
    a, b = mass_matrix(q)[0]
    c21, d = mass_matrix(q)[1]
    determinant = a * d - b * c21
    # 二元线性方程的消元结果，仅用于此自包含教学模型。
    return [(d * rhs[0] - b * rhs[1]) / determinant,
            (a * rhs[1] - c21 * rhs[0]) / determinant]


def potential(q):
    """质心高度给出的重力势能，J；独立用于差分核对 G(q)。"""
    y1 = -LC1 * math.cos(q[0])
    y2 = -L1 * math.cos(q[0]) - LC2 * math.cos(q[0] + q[1])
    return G * (M1 * y1 + M2 * y2)


def kinetic_from_bodies(q, velocity):
    """分别计算质心平动与刚体自转动能；不调用 mass_matrix。"""
    w1, w2 = velocity[0], sum(velocity)
    v1 = [LC1 * math.cos(q[0]) * w1, LC1 * math.sin(q[0]) * w1]
    v2 = [L1 * math.cos(q[0]) * w1 + LC2 * math.cos(sum(q)) * w2,
          L1 * math.sin(q[0]) * w1 + LC2 * math.sin(sum(q)) * w2]
    return .5 * (M1 * dot(v1, v1) + M2 * dot(v2, v2) + IC1 * w1**2 + IC2 * w2**2)


def endpoint(q):
    return [L1 * math.sin(q[0]) + L2 * math.sin(sum(q)),
            -L1 * math.cos(q[0]) - L2 * math.cos(sum(q))]


class ChapterExamples(unittest.TestCase):
    def assertVectorClose(self, actual, expected, tolerance=1e-9):
        self.assertEqual(len(actual), len(expected))
        for a, e in zip(actual, expected):
            self.assertAlmostEqual(a, e, delta=tolerance)

    def test_matrix_table(self):
        for elbow, row1, row2 in [(0, [1.92, .60], [.60, .24]),
                                  (math.pi / 2, [1.2, .24], [.24, .24]),
                                  (math.pi, [.48, -.12], [-.12, .24])]:
            matrix = mass_matrix([0, elbow])
            self.assertVectorClose(matrix[0], row1)
            self.assertVectorClose(matrix[1], row2)

    def test_free_elbow(self):
        acceleration = forward([0, 0], [0, 0], [1, 0])
        self.assertVectorClose(acceleration, [50 / 21, -125 / 21])
        self.assertAlmostEqual(sum(acceleration), -25 / 7)
        self.assertVectorClose(matvec(mass_matrix([0, 0]), acceleration), [1, 0])

    def test_elbow_held(self):
        self.assertVectorClose(required_motor([0, 0], [0, 0], [25 / 48, 0]), [1, .3125])
        self.assertVectorClose(forward([0, 0], [0, 0], [1, .3125]), [25 / 48, 0])

    def test_gravity_table_and_potential_gradient(self):
        self.assertVectorClose(gravity_compensation([math.pi / 2, 0]), [23.544, 5.886])
        self.assertVectorClose(gravity_compensation([math.pi / 2, -math.pi / 2]), [17.658, 0])
        h = 1e-6
        for q in [[0, 0], [.4, -.7], [math.pi / 2, 0], [-.5, .8]]:
            finite_difference = []
            for i in range(2):
                plus, minus = q.copy(), q.copy()
                plus[i] += h
                minus[i] -= h
                finite_difference.append((potential(plus) - potential(minus)) / (2 * h))
            self.assertVectorClose(gravity_compensation(q), finite_difference, 1e-7)

    def test_velocity_scaling(self):
        q = [0, math.pi / 2]
        self.assertVectorClose(velocity_terms(q, [0, 0]), [0, 0])
        self.assertVectorClose(velocity_terms(q, [1, 2]), [-2.88, .36])
        self.assertVectorClose(velocity_terms(q, [2, 4]), [-11.52, 1.44])
        self.assertVectorClose([DAMPING[i] * [2, 4][i] for i in range(2)], [.4, .8])

    def test_combined_example_and_forward_inverse(self):
        q, velocity = [0, math.pi / 2], [1, 2]
        self.assertVectorClose(required_motor(q, velocity, [1, 0]), [4.406, 6.886])
        self.assertVectorClose(forward(q, velocity, [4.406, 6.886]), [1, 0])
        for q, velocity, acc, ext in [([.3, -.7], [1, -2], [-3, 1], [.2, -.3]),
                                     ([-.9, .4], [-2, 1], [2, -1], [-1, .5])]:
            motor = required_motor(q, velocity, acc, ext)
            self.assertVectorClose(forward(q, velocity, motor, ext), acc)

    def test_mass_matrix_against_body_kinetic_energy(self):
        for q in [[0, 0], [.7, -1.2], [-.8, 2.3]]:
            for velocity in [[1, 0], [0, 1], [1, 2], [-2, .7]]:
                matrix_energy = .5 * dot(velocity, matvec(mass_matrix(q), velocity))
                self.assertAlmostEqual(matrix_energy, kinetic_from_bodies(q, velocity), delta=1e-10)

    def test_velocity_terms_against_matrix_derivatives(self):
        # Christoffel 组合，以数值导数独立检查速度乘积项和符号。
        h = 1e-6
        for q, velocity in [([.4, .9], [1, 2]), ([-.7, -.3], [-2, .5])]:
            derivatives = []
            for coordinate in range(2):
                plus, minus = q.copy(), q.copy()
                plus[coordinate] += h
                minus[coordinate] -= h
                mp, mm = mass_matrix(plus), mass_matrix(minus)
                derivatives.append([[(mp[i][j] - mm[i][j]) / (2 * h)
                                     for j in range(2)] for i in range(2)])
            numeric = [sum(.5 * (derivatives[k][i][j] + derivatives[j][i][k]
                                - derivatives[i][j][k]) * velocity[j] * velocity[k]
                           for j in range(2) for k in range(2)) for i in range(2)]
            self.assertVectorClose(velocity_terms(q, velocity), numeric, 1e-7)

    def test_external_force_by_endpoint_displacement(self):
        q, force, h = [math.pi / 2, 0], [0, -10], 1e-6
        external = []
        for i in range(2):
            plus, minus = q.copy(), q.copy()
            plus[i] += h
            minus[i] -= h
            pp, pm = endpoint(plus), endpoint(minus)
            derivative = [(pp[j] - pm[j]) / (2 * h) for j in range(2)]
            external.append(dot(derivative, force))
        self.assertVectorClose(external, [-12, -6], 1e-7)
        self.assertVectorClose(required_motor(q, [0, 0], [0, 0], [-12, -6]), [35.544, 11.886])
        self.assertVectorClose(forward(q, [0, 0], [35.544, 11.886], [-12, -6]), [0, 0])

    def test_positive_definite_even_at_kinematic_singularity(self):
        for elbow in [i * math.pi / 12 for i in range(-12, 13)]:
            matrix = mass_matrix([.2, elbow])
            self.assertAlmostEqual(matrix[0][1], matrix[1][0])
            self.assertGreater(matrix[0][0], 0)
            self.assertGreater(matrix[0][0] * matrix[1][1] - matrix[0][1]**2, 0)
        matrix = mass_matrix([0, 0])
        self.assertAlmostEqual(matrix[0][0] * matrix[1][1] - matrix[0][1]**2, .1008)
        # 伸直下垂时，末端 x/y 位置雅可比为 [[1.2, .6], [0, 0]]。
        jacobian = [[L1 + L2, L2], [0, 0]]
        self.assertEqual(jacobian[0][0] * jacobian[1][1] - jacobian[0][1] * jacobian[1][0], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
