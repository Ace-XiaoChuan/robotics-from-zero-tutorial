import math
import numpy as np


def get_rotation_matrix_z(theta):
    theta_radians = theta / 180 * math.pi
    cos_theta = math.cos(theta_radians)
    sin_theta = math.sin(theta_radians)
    target_matrix = np.array(
        [[cos_theta, -sin_theta, 0], [sin_theta, cos_theta, 0], [0, 0, 1]]
    )
    target_matrix = np.round(target_matrix, decimals=5)
    return target_matrix


def get_rotation_matrix_y(theta):
    theta_radians = theta / 180 * math.pi
    cos_theta = math.cos(theta_radians)
    sin_theta = math.sin(theta_radians)
    target_matrix = np.array(
        [
            [cos_theta, 0, sin_theta],
            [0, 1, 0],
            [-sin_theta, 0, cos_theta],
        ]
    )
    target_matrix = np.round(target_matrix, decimals=5)
    return target_matrix


def get_rotation_matrix_x(theta):
    theta_radians = theta / 180 * math.pi
    cos_theta = math.cos(theta_radians)
    sin_theta = math.sin(theta_radians)
    target_matrix = np.array(
        [
            [1, 0, 0],
            [0, cos_theta, -sin_theta],
            [0, sin_theta, cos_theta],
        ]
    )
    target_matrix = np.round(target_matrix, decimals=5)
    return target_matrix


def get_homogeneous_matrix(R, t):

    T = np.eye(4)
    T[0:3, 0:3] = R
    T[0:3, 3] = t
    return T


my_R = get_rotation_matrix_z(90)
my_t = np.array([1, 2, 3])
p = np.array([1, 0, 0, 1])

T = get_homogeneous_matrix(my_R, my_t)
print("齐次变换矩阵 T 是：\n", T)
print("点乘结果是：\n", T @ p)
