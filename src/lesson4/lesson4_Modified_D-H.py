import numpy as np


# 1. 定义一个函数，专门用来生成 D-H 变换矩阵 (基于 Craig 改进型 D-H)
def get_dh_matrix(a, alpha, d, theta):
    """
    输入四个DH参数，生成DH变换矩阵
    Args:
        a : 连杆长度：两个相邻旋转轴（Z 轴）之间的最短距离（公垂线长度）。
        alpha : 连杆扭角：两个相邻旋转轴（Z 轴）在空间中并不一定是平行的，这个角就是它们之间的夹角。
        d : 连杆偏距：沿着当前关节的旋转轴（Z 轴）滑动，从上一个连杆的垂足走到下一个连杆的垂足所需要的距离。
        theta : 关节角：电机实际转动的角度。也就是绕着当前关节的旋转轴（Z 轴）转动，让前后两个坐标系的 X 轴对齐所需要的角度。
    """
    matrix = np.array(
        [
            [np.cos(theta), -np.sin(theta), 0, a],
            [
                np.sin(theta) * np.cos(alpha),
                np.cos(theta) * np.cos(alpha),
                -np.sin(alpha),
                -d * np.sin(alpha),
            ],
            [
                np.sin(theta) * np.sin(alpha),
                np.cos(theta) * np.sin(alpha),
                np.cos(alpha),
                d * np.cos(alpha),
            ],
            [0, 0, 0, 1],
        ]
    )
    return matrix


# 2. 设置我们这台 2R 机械臂的物理参数
a1 = 10.0  # 第一节机械臂的长度
a2 = 5.0  # 第二节机械臂的长度

# 假设当前电机的角度 (把角度转化为弧度以便于计算)
# 假设关节1转了 30 度，关节2转了 45 度
theta1 = np.radians(30)
theta2 = np.radians(45)

T1 = get_dh_matrix(0, 0, 0, theta1)  # 底座到关节1
T2 = get_dh_matrix(a1, 0, 0, theta2)
T3 = get_dh_matrix(a2, 0, 0, 0)
T_total = T1 @ T2 @ T3

print("最终的 4x4 变换矩阵是：\n", np.round(T_total, 3))

x = T_total[0, 3]
y = T_total[1, 3]

print(f"\n推算出的末端坐标为: X = {x:.3f}, Y = {y:.3f}")

print("---接下来进行几何角度的验算---")

a1_x = a1 * np.cos(theta1)
a1_y = a1 * np.sin(theta1)
a2_x = a2 * np.cos(theta1 + theta2)
a2_y = a2 * np.sin(theta1 + theta2)

print(f"x_total:{a1_x+a2_x},\ny_total:{a1_y+a2_y}")
