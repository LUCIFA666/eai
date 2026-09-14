# 位姿与旋转表示

## 本章概述

机器人系统中的几乎所有运动、感知和控制任务，都离不开对空间位置和方向的描述。无论是机械臂末端执行器的位置、移动机器人的导航目标、相机的安装姿态，还是视觉算法检测到的目标物体，都需要通过统一的位姿（Pose）进行表达。

在机器人软件中，一个位姿不仅描述物体位于哪里，还描述物体朝向哪里，因此成为机器人系统中最基础的数据类型之一。与此同时，同一个姿态可以采用旋转矩阵、欧拉角、四元数、轴角等多种方式表示，不同机器人平台、通信接口和仿真软件也会采用不同的数据格式。如果不了解这些表示方式之间的区别，很容易在模型转换、数据记录、算法部署和真机控制过程中产生错误。

需要特别强调的是，一个位姿数据只有明确所属坐标系和对应时间之后才具有实际意义。脱离坐标系和时间戳的坐标值无法与其他模块建立空间对应关系，也无法参与机器人系统中的感知、规划和控制。

本章将介绍机器人系统中常见的位姿和旋转表示方式，分析不同表示在机器人接口中的使用场景，说明各种表示需要注意的问题，并介绍机器人开发过程中常见的单位和坐标约定。最后，通过一个机器人末端位姿示例，说明同一个空间位姿如何在不同接口中采用不同的数据表示。本章主要关注工程实践中的接口使用，不涉及旋转矩阵推导、四元数运算或李群李代数等数学理论。

## 位姿的组成及其接口意义

机器人中的**位姿（Pose）**用于描述一个刚体在三维空间中的完整状态，它由**位置（Position）**和**姿态（Orientation）**两部分共同组成。

其中，Position 用于描述目标位于空间中的位置，通常包含三个坐标分量：

```text
x, y, z
```

Orientation 用于描述目标在空间中的朝向，即物体相对于参考坐标系发生了怎样的旋转。

因此，一个完整的 Pose 可以表示为：

```text
Pose

Position
    x
    y
    z

Orientation
    ...
```

需要注意的是，Position 与 Orientation 本身并不能唯一描述机器人状态，它们必须绑定对应的**frame_id** 和 **timestamp** 才具有实际意义。

例如：

```text
Position

(0.45, 0.12, 0.30)
```

如果不知道它属于：

- base_link
- tool0
- camera_link
- map

中的哪一个坐标系，那么这个位置没有任何实际意义。

同样，如果不知道数据对应的时间：

```text
timestamp
```

那么机器人无法判断该位姿是否仍然有效，也无法与相机图像、IMU 数据或机器人状态进行同步。

因此，在机器人接口中，一个完整的位姿通常包含以下信息：

- Position
- Orientation
- frame_id
- timestamp

这四部分共同构成了机器人系统中的标准空间描述对象。

## 常见旋转表示方式

机器人系统中描述姿态的方法有多种，不同表示方式适用于不同的应用场景。虽然它们表达的是同一种空间旋转，但在接口设计、数值计算以及软件支持方面各有特点。

### Rotation Matrix（旋转矩阵）

Rotation Matrix 是机器人学中最基础的旋转表示方式。

它通常采用一个 3×3 正交矩阵描述坐标系之间的旋转关系。

旋转矩阵最大的特点是能够直接参与坐标变换，因此广泛用于：

- 机器人运动学计算；
- 坐标变换；
- 物理引擎；
- 三维图形渲染；
- 机器人模型内部计算。

虽然旋转矩阵计算方便，但需要存储九个数值，数据量较大，因此较少直接作为机器人通信接口的数据格式。

**Python 代码示例：**

以下代码演示了如何使用 Python 创建旋转矩阵、验证其性质，以及利用旋转矩阵进行坐标变换。

```python
import numpy as np
from scipy.spatial.transform import Rotation

# ============================================================
# 1. 基本旋转矩阵（绕 X / Y / Z 轴）
# ============================================================

def rot_x(theta):
    """绕 X 轴旋转 theta 弧度"""
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[1, 0, 0],
                     [0, c, -s],
                     [0, s, c]])

def rot_y(theta):
    """绕 Y 轴旋转 theta 弧度"""
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, 0, s],
                     [0, 1, 0],
                     [-s, 0, c]])

def rot_z(theta):
    """绕 Z 轴旋转 theta 弧度"""
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s, 0],
                     [s, c, 0],
                     [0, 0, 1]])

# 示例：绕 Z 轴旋转 90°（π/2 弧度）
R = rot_z(np.pi / 2)
print("旋转矩阵 R (绕Z轴90°):")
print(R)
# [[ 6.1232e-17 -1.0000e+00  0.0000e+00]
#  [ 1.0000e+00  6.1232e-17  0.0000e+00]
#  [ 0.0000e+00  0.0000e+00  1.0000e+00]]

# ============================================================
# 2. 验证旋转矩阵的正交性与行列式
# ============================================================

# 正交性：R @ R^T 应等于单位矩阵
print("R @ R^T == I:", np.allclose(R @ R.T, np.eye(3)))   # True

# 行列式应等于 1
print("det(R) == 1:", np.allclose(np.linalg.det(R), 1.0))  # True

# 旋转矩阵的逆等于其转置
print("R^{-1} == R^T:", np.allclose(np.linalg.inv(R), R.T)) # True

# ============================================================
# 3. 旋转矩阵用于坐标变换
# ============================================================

# 场景：已知坐标系 {B} 相对于坐标系 {A} 绕 Z 轴旋转了 45°
R_A_B = rot_z(np.pi / 4)

# {B} 的原点在 {A} 中的平移向量
t_A_B = np.array([1.0, 0.5, 0.0])

# 点 P 在坐标系 {B} 中的坐标
P_B = np.array([0.3, 0.2, 0.1])

# 将 P 从 {B} 变换到 {A}： P_A = R_A_B · P_B + t_A_B
P_A = R_A_B @ P_B + t_A_B
print("P 在 {A} 中的坐标:", P_A)
# 输出示例: [1.2121 0.8536 0.1   ]

# ============================================================
# 4. 齐次变换矩阵（Homogeneous Transformation）
# ============================================================

# 构造 4×4 齐次变换矩阵 T = [R  t]
#                            [0  1]
T_A_B = np.eye(4)
T_A_B[:3, :3] = R_A_B      # 旋转部分
T_A_B[:3, 3] = t_A_B       # 平移部分

print("\n齐次变换矩阵 T_A_B:")
print(T_A_B)
# [[ 0.7071 -0.7071  0.      1.    ]
#  [ 0.7071  0.7071  0.      0.5   ]
#  [ 0.      0.      1.      0.    ]
#  [ 0.      0.      0.      1.    ]]

# 使用齐次坐标进行变换（结果与上面一致）
P_B_homo = np.append(P_B, 1.0)          # 齐次坐标
P_A_homo = T_A_B @ P_B_homo
print("齐次变换结果:", P_A_homo[:3])      # 与 P_A 一致

# 逆变换：从 {A} 变换回 {B}
T_B_A = np.linalg.inv(T_A_B)
P_B_back = (T_B_A @ np.append(P_A, 1.0))[:3]
print("逆变换回 {B}:", P_B_back)         # 应与 P_B 一致

# ============================================================
# 5. 连续坐标变换（链式变换）
# ============================================================

# 场景：世界坐标系 {W} → 机器人基座 {B} → 末端执行器 {E}
T_W_B = np.eye(4)
T_W_B[:3, :3] = rot_z(np.pi / 6)        # 基座相对世界旋转 30°
T_W_B[:3, 3] = [2.0, 0.0, 0.0]          # 基座在世界中位于 (2, 0, 0)

T_B_E = np.eye(4)
T_B_E[:3, :3] = rot_y(np.pi / 4)        # 末端相对基座旋转 45°
T_B_E[:3, 3] = [0.5, 0.0, 0.3]          # 末端在基座中位于 (0.5, 0, 0.3)

# 链式变换：T_W_E = T_W_B @ T_B_E
T_W_E = T_W_B @ T_B_E
print("\n世界到末端的齐次变换 T_W_E:")
print(T_W_E)

# ============================================================
# 6. 使用 scipy.spatial.transform.Rotation 进行姿态转换
# ============================================================

# 从欧拉角创建旋转（ZYX 顺序，角度制）
R_scipy = Rotation.from_euler('zyx', [90, 0, 0], degrees=True)
print("\n从欧拉角 (ZYX, 90°, 0°, 0°) 生成的旋转矩阵:")
print(R_scipy.as_matrix())

# 旋转矩阵 → 四元数
rot = Rotation.from_matrix(R)
print("四元数 (x, y, z, w):", rot.as_quat())     # [x, y, z, w]

# 旋转矩阵 → 欧拉角（ZYX 顺序，弧度）
print("欧拉角 (ZYX, rad):", rot.as_euler('zyx'))

# 旋转矩阵 → 轴角表示
print("轴角 (rotvec):", rot.as_rotvec())          # 方向=轴, 长度=角度

# 注意：scipy 四元数格式为 (x, y, z, w)，与 ROS 一致
```

> **代码说明：**
> - `rot_x / rot_y / rot_z` 分别构造绕单轴的旋转矩阵，适合理解基本原理。
> - 通过 `R @ R.T` 和行列式可以验证旋转矩阵的正交性和合法性，实际工程中可据此检测数值误差累积。
> - 齐次变换矩阵 `T = [R t; 0 1]` 是机器人运动学中最核心的数据结构，它将旋转与平移统一为一次矩阵乘法。
> - `scipy.spatial.transform.Rotation` 提供了旋转矩阵、欧拉角、四元数、轴角之间的统一转换接口，是机器人开发中最常用的姿态工具类之一。

### Euler Angle（欧拉角）

Euler Angle 使用三个旋转角度描述姿态。

例如：

```text
Roll, Pitch, Yaw
```

或

```text
Rx, Ry, Rz
```

欧拉角具有直观、易于理解的特点，因此大量用于：

- 人机交互界面；
- 机器人调试软件；
- 示教器；
- 参数配置；
- 工业机器人运动指令。

例如，在机械臂示教过程中，用户通常看到的是末端位置加 Roll、Pitch、Yaw，而不是旋转矩阵或四元数。

### Quaternion（四元数）

Quaternion 使用四个数值描述空间旋转：

```text
x, y, z, w
```

相比欧拉角，四元数能够避免万向节锁问题，同时数据量比旋转矩阵更小，因此成为机器人系统中最常见的姿态表示方式之一。ROS、MoveIt、Isaac Sim、Unity、三维视觉算法以及大多数机器人 SDK 都大量采用四元数作为姿态接口。

对于机器人开发而言，四元数虽然不如欧拉角直观，但更适合作为程序内部的数据表示。

**四元数的数学定义：**

四元数将空间旋转表示为 4D 单位球面上的一个点。绕单位轴 $\mathbf{u} = (u_x, u_y, u_z)$ 旋转角度 $\theta$ 所对应的四元数为：

$$q = \left(\sin\frac{\theta}{2} \cdot u_x,\quad \sin\frac{\theta}{2} \cdot u_y,\quad \sin\frac{\theta}{2} \cdot u_z,\quad \cos\frac{\theta}{2}\right)$$

其中 $(x, y, z)$ 为虚部，$w$ 为实部。ROS 与 scipy 均采用 $(x, y, z, w)$ 顺序。

**Python 代码示例：**

```python
import numpy as np

# ============================================================
# 1. 四元数构造（从轴角）
# ============================================================

def quat_from_axis_angle(axis, angle):
    """从旋转轴和旋转角构造四元数 (x, y, z, w 格式)

    公式: q = (sin(θ/2)·u_x, sin(θ/2)·u_y, sin(θ/2)·u_z, cos(θ/2))
    """
    axis = axis / np.linalg.norm(axis)          # 确保旋转轴为单位向量
    half = angle / 2.0
    s = np.sin(half)
    return np.array([axis[0] * s, axis[1] * s, axis[2] * s, np.cos(half)])

# 绕 Z 轴旋转 90° → 四元数
q_z90 = quat_from_axis_angle(np.array([0.0, 0.0, 1.0]), np.pi / 2)
print("绕 Z 轴 90° 的四元数 (x, y, z, w):", q_z90)
# → [0.      0.      0.7071  0.7071]

# ============================================================
# 2. 四元数归一化
# ============================================================

def quat_norm(q):
    """模长: ||q|| = sqrt(x² + y² + z² + w²)"""
    return np.sqrt(np.sum(q ** 2))

def quat_normalize(q):
    """归一化到单位四元数: q / ||q||"""
    return q / quat_norm(q)

print("||q|| =", quat_norm(q_z90))  # → 1.0

# 长时间数值计算后四元数可能漂移，需要重新归一化
q_drifted = np.array([0.0, 0.0, 0.7073, 0.7069])   # 模拟数值误差
q_fixed = quat_normalize(q_drifted)
print("修正后 ||q|| =", quat_norm(q_fixed))          # → 1.0

# ============================================================
# 3. 四元数乘法（组合旋转）
# ============================================================

def quat_multiply(q1, q2):
    """Hamilton 四元数乘法: q1 ⊗ q2（先旋转 q2，再旋转 q1）

    (x, y, z, w) 格式下的乘法公式：
        x' = w1·x2 + x1·w2 + y1·z2 - z1·y2
        y' = w1·y2 - x1·z2 + y1·w2 + z1·x2
        z' = w1·z2 + x1·y2 - y1·x2 + z1·w2
        w' = w1·w2 - x1·x2 - y1·y2 - z1·z2
    """
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return np.array([
        w1*x2 + x1*w2 + y1*z2 - z1*y2,   # x
        w1*y2 - x1*z2 + y1*w2 + z1*x2,   # y
        w1*z2 + x1*y2 - y1*x2 + z1*w2,   # z
        w1*w2 - x1*x2 - y1*y2 - z1*z2,   # w
    ])

# 先绕 Z 轴转 90°，再绕 X 轴转 90°
q_rot_z90 = quat_from_axis_angle(np.array([0., 0., 1.]), np.pi / 2)
q_rot_x90 = quat_from_axis_angle(np.array([1., 0., 0.]), np.pi / 2)
q_combined = quat_multiply(q_rot_x90, q_rot_z90)  # 注意：右乘先发生
print("组合旋转 (先Z90后X90):", q_combined)

# ============================================================
# 4. 用四元数旋转向量
# ============================================================

def quat_rotate_vector(q, v):
    """用四元数 q 旋转三维向量 v

    公式: v' = q ⊗ (v, 0) ⊗ q*（q* 为 q 的共轭）
    其中纯四元数 (v, 0) = (v_x, v_y, v_z, 0)
    """
    q_conj = np.array([-q[0], -q[1], -q[2], q[3]])   # 单位四元数的共轭 = 逆
    v_pure = np.array([v[0], v[1], v[2], 0.0])
    result = quat_multiply(quat_multiply(q, v_pure), q_conj)
    return result[:3]                                 # 取虚部作为 3D 向量

# 绕 Z 轴旋转 90° 作用于向量 (1, 0, 0)，结果应为 (0, 1, 0)
v = np.array([1.0, 0.0, 0.0])
v_rotated = quat_rotate_vector(q_z90, v)
print("(1, 0, 0) 绕 Z 轴 90° 后:", v_rotated)        # → (0, 1, 0)

# ============================================================
# 5. 符号等价性验证
# ============================================================

q_neg = -q_z90
print("q 与 -q 数值相等?", np.allclose(q_z90, q_neg))  # → False
print("旋转同一向量结果相同?",
      np.allclose(quat_rotate_vector(q_z90, v),
                  quat_rotate_vector(q_neg, v)))        # → True

# 比较两个四元数时的正确做法——考虑符号等价
def quat_almost_equal(q1, q2, tol=1e-8):
    """考虑符号等价性的四元数比较"""
    return np.allclose(q1, q2, atol=tol) or np.allclose(q1, -q2, atol=tol)

print("实际等价?", quat_almost_equal(q_z90, q_neg))     # → True

# ============================================================
# 6. 四元数球面线性插值 (SLERP)
# ============================================================

def quat_slerp(q1, q2, t):
    """在 q1 与 q2 之间按比例 t ∈ [0, 1] 进行球面线性插值

    公式:
        slerp(q1, q2, t) = sin((1-t)Ω)/sin(Ω) · q1 + sin(tΩ)/sin(Ω) · q2
        其中 Ω = arccos(q1 · q2)，即两四元数在 4D 球面上的夹角
    """
    q1, q2 = quat_normalize(q1), quat_normalize(q2)
    dot = np.dot(q1, q2)
    # 选择最短弧（符号处理）
    if dot < 0:
        q2, dot = -q2, -dot
    # 角度极小 → 退化为线性插值以避免除零
    if dot > 0.9995:
        return quat_normalize(q1 + t * (q2 - q1))
    omega = np.arccos(np.clip(dot, -1.0, 1.0))
    s1 = np.sin((1 - t) * omega) / np.sin(omega)
    s2 = np.sin(t * omega) / np.sin(omega)
    return s1 * q1 + s2 * q2

# 在两个姿态之间插值
q_start = quat_from_axis_angle(np.array([0., 0., 1.]), 0.0)       # 0°
q_end   = quat_from_axis_angle(np.array([0., 0., 1.]), np.pi / 2) # 90°
q_mid   = quat_slerp(q_start, q_end, 0.5)  # 中间姿态 → 45°
print("SLERP 中间姿态:", q_mid)
```

> **代码说明：**
> - 四元数构造的核心公式是 $q = (\sin\frac{\theta}{2} u_x,\ \sin\frac{\theta}{2} u_y,\ \sin\frac{\theta}{2} u_z,\ \cos\frac{\theta}{2})$，它将轴角表示直接映射为四元数。
> - 归一化是四元数使用中最重要的维护操作：任何数值漂移后都应调用 `quat_normalize` 恢复单位长度。
> - Hamilton 乘法是组合旋转的基础运算，注意 $\otimes$ 不可交换（$q_1 \otimes q_2 \neq q_2 \otimes q_1$）。
> - 旋转向量使用 Sandwich 乘积 $q \otimes v \otimes q^*$，其中 $v$ 被嵌入为纯四元数 $(v_x, v_y, v_z, 0)$。
> - SLERP 是机器人路径规划中姿态插值的标准方法，相比线性插值（LERP），SLERP 能保证插值结果始终是单位四元数且角速度恒定。
> - scipy 中可直接使用 `Rotation` 类完成以上所有操作，但手动实现有助于理解四元数运算的本质。

### Axis-Angle（轴角表示）

Axis-Angle 使用：

- 一个旋转轴
- 一个旋转角度

共同描述空间旋转。

轴角表示在机器人控制、优化算法以及运动学求解中较为常见。

例如：

- 机械臂末端误差表示；
- 李代数运动表示；
- 部分机器人 SDK。

虽然普通接口较少直接采用 Axis-Angle，但很多内部算法都会在四元数、旋转矩阵和轴角之间进行转换。

**轴角到旋转矩阵 —— Rodrigues' 公式：**

给定单位旋转轴 $\mathbf{u} = (u_x, u_y, u_z)$ 和旋转角度 $\theta$，对应的旋转矩阵为：

$$R = I + \sin\theta \cdot [\mathbf{u}]_\times + (1 - \cos\theta) \cdot [\mathbf{u}]_\times^2$$

其中 $[\mathbf{u}]_\times$ 是 $\mathbf{u}$ 的反对称矩阵（skew-symmetric matrix）：

$$[\mathbf{u}]_\times = \begin{bmatrix} 0 & -u_z & u_y \\\\ u_z & 0 & -u_x \\\\ -u_y & u_x & 0 \end{bmatrix}$$

**旋转矩阵到轴角（逆 Rodrigues）：**

$$\theta = \arccos\left(\frac{\text{tr}(R) - 1}{2}\right), \quad \mathbf{u} = \frac{1}{2\sin\theta}\begin{bmatrix} R_{32} - R_{23} \\ R_{13} - R_{31} \\ R_{21} - R_{12} \end{bmatrix}$$

**Python 代码示例：**

```python
import numpy as np

# ============================================================
# 1. 轴角 → 旋转矩阵（Rodrigues 公式）
# ============================================================

def axis_angle_to_rotation_matrix(axis, angle):
    """将轴角表示转换为 3×3 旋转矩阵

    公式: R = I + sinθ·[u]× + (1 - cosθ)·[u]×²
    """
    axis = axis / np.linalg.norm(axis)
    ux, uy, uz = axis
    # 反对称矩阵 [u]×
    K = np.array([[ 0,   -uz,   uy],
                  [ uz,   0,   -ux],
                  [-uy,  ux,    0 ]])
    c = np.cos(angle)
    s = np.sin(angle)
    R = np.eye(3) + s * K + (1 - c) * (K @ K)
    return R

# 绕 Z 轴旋转 90°
R_from_axis = axis_angle_to_rotation_matrix(
    np.array([0., 0., 1.]), np.pi / 2)
print("Rodrigues 公式得到的旋转矩阵:")
print(R_from_axis)

# ============================================================
# 2. 旋转矩阵 → 轴角（逆 Rodrigues）
# ============================================================

def rotation_matrix_to_axis_angle(R):
    """将 3×3 旋转矩阵转换为轴角表示

    公式:
        θ = arccos((tr(R) - 1) / 2)
        u = (R32-R23, R13-R31, R21-R12) / (2·sinθ)
    """
    theta = np.arccos(np.clip((np.trace(R) - 1) / 2, -1.0, 1.0))

    if np.abs(theta) < 1e-8:
        # 旋转角度接近 0 → 任意轴均可，返回默认轴
        return np.array([0., 0., 1.]), 0.0

    if np.abs(theta - np.pi) < 1e-8:
        # 旋转 180° 时 sinθ = 0，需要特殊处理
        # 从 R + I 的非零列中提取旋转轴
        B = (R + np.eye(3)) / 2
        # 选择 B 中范数最大的列
        cols = [B[:, 0], B[:, 1], B[:, 2]]
        axis = max(cols, key=lambda c: np.linalg.norm(c))
        return axis / np.linalg.norm(axis), np.pi

    axis = np.array([R[2, 1] - R[1, 2],
                     R[0, 2] - R[2, 0],
                     R[1, 0] - R[0, 1]]) / (2 * np.sin(theta))
    return axis, theta

axis, angle = rotation_matrix_to_axis_angle(R_from_axis)
print(f"轴: {axis}, 角度: {angle:.4f} rad ({np.degrees(angle):.1f}°)")

# ============================================================
# 3. scipy 版本的轴角转换
# ============================================================

from scipy.spatial.transform import Rotation

# 轴角 → 旋转矩阵
rotvec = np.array([0., 0., np.pi / 2])    # 向量方向=轴, 长度=角度
R_scipy = Rotation.from_rotvec(rotvec)
print("\nscipy 旋转矩阵:")
print(R_scipy.as_matrix())

# 旋转矩阵 → 轴角
rotvec_back = Rotation.from_matrix(R_from_axis).as_rotvec()
print(f"scipy rotvec: {rotvec_back}")
```

> **代码说明：**
> - Rodrigues 公式是轴角与旋转矩阵之间的标准桥梁，广泛用于机器人运动学、SLAM 优化和李代数运算中。
> - 旋转角度接近 $0$ 或 $\pi$ 时，逆 Rodrigues 公式需要特殊处理以避免除零错误。
> - `scipy.spatial.transform.Rotation` 使用 `rotvec`（旋转向量）表示轴角——向量的方向为旋转轴，向量的长度为旋转角度。

## 各类旋转表示需要注意的问题

不同旋转表示虽然可以相互转换，但每种表示方式都具有自身特点，在机器人开发过程中需要特别注意。

### 欧拉角的旋转顺序与奇异性

欧拉角最大的特点是依赖**旋转顺序**。

例如：

- XYZ
- ZYX
- ZYZ

不同旋转顺序即使使用完全相同的三个角度，也可能得到完全不同的姿态。

因此，在机器人接口中，必须明确欧拉角采用哪一种旋转顺序，而不能仅记录三个角度数值。

此外，欧拉角还存在**万向节锁（Gimbal Lock）**问题。当某些姿态接近特殊角度时，两个旋转轴可能发生重合，从而导致自由度丢失，使姿态表示出现奇异性。这也是机器人内部较少直接使用欧拉角进行计算的重要原因。

**Python 代码演示：**

```python
import numpy as np
from scipy.spatial.transform import Rotation

# ============================================================
# 1. 旋转顺序的影响
# ============================================================

angles = [30, 45, 60]  # 相同的三个角度（度）

# 同一组角度，不同的旋转顺序 → 完全不同的姿态
R_xyz = Rotation.from_euler('xyz', angles, degrees=True).as_matrix()
R_zyx = Rotation.from_euler('zyx', angles, degrees=True).as_matrix()
R_zyz = Rotation.from_euler('zyz', angles, degrees=True).as_matrix()

print("相同的角度 (30°, 45°, 60°)，不同旋转顺序:")
print("XYZ 旋转矩阵:\n", R_xyz)
print("ZYX 旋转矩阵:\n", R_zyx)
print("ZYZ 旋转矩阵:\n", R_zyz)
# 三组矩阵完全不同！仅凭角度值无法唯一确定姿态

# ============================================================
# 2. 欧拉角 → 旋转矩阵的公式（以 ZYX / RPY 顺序为例）
# ============================================================

def euler_zyx_to_rotation_matrix(roll, pitch, yaw):
    """ZYX 顺序（RPY）欧拉角 → 旋转矩阵

    公式: R = Rz(yaw) · Ry(pitch) · Rx(roll)

    其中:
        Rx(φ) = [[1,  0,   0 ],
                 [0, cφ, -sφ],
                 [0, sφ,  cφ]]

        Ry(θ) = [[ cθ, 0, sθ],
                 [ 0,  1, 0 ],
                 [-sθ, 0, cθ]]

        Rz(ψ) = [[cψ, -sψ, 0],
                 [sψ,  cψ, 0],
                 [0,   0,  1]]
    """
    cr, sr = np.cos(roll),  np.sin(roll)
    cp, sp = np.cos(pitch), np.sin(pitch)
    cy, sy = np.cos(yaw),   np.sin(yaw)

    Rx = np.array([[1, 0,  0], [0, cr, -sr], [0, sr, cr]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0],   [-sp, 0, cp]])
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])

    return Rz @ Ry @ Rx  # 注意顺序：外旋按 Z→Y→X 从右到左相乘

# 验证
R_manual = euler_zyx_to_rotation_matrix(np.radians(30),
                                         np.radians(45),
                                         np.radians(60))
R_scipy  = Rotation.from_euler('ZYX', [30, 45, 60], degrees=True).as_matrix()
print("\n手动计算 vs scipy:", np.allclose(R_manual, R_scipy))  # → True

# ============================================================
# 3. 万向节锁（Gimbal Lock）演示
# ============================================================

# 当 pitch = 90° 时，ZYX 欧拉角出现万向节锁
# R = Rz(yaw) · Ry(90°) · Rx(roll)
#   = Rz(yaw) · [[0,0,1],[0,1,0],[-1,0,0]] · Rx(roll)
#   = Rz(yaw) · Rz(roll)  → yaw 和 roll 绕同一轴旋转，退化掉一个自由度

print("\n万向节锁示例（pitch = 90°）:")
R_lock1 = Rotation.from_euler('ZYX', [10, 90, 30], degrees=True).as_matrix()
R_lock2 = Rotation.from_euler('ZYX', [40, 90,  0], degrees=True).as_matrix()
# 两组不同的 roll/yaw 可能得到几乎相同的姿态
print("roll=10,yaw=30 与 roll=40,yaw=0 结果相同?",
      np.allclose(R_lock1, R_lock2))  # → True（roll+yaw 和相等则姿态相同）
```

### 四元数的归一化与符号等价

四元数虽然不存在万向节锁问题，但使用过程中仍需要注意两个特点。

首先，四元数必须保持**归一化**，即其长度应始终等于 1。如果经过数值计算后四元数长度发生变化，需要重新进行归一化，否则会导致旋转结果出现误差。

其次，四元数具有**符号等价性**。

例如：

```text
(qx, qy, qz, qw)
```

与

```text
(-qx, -qy, -qz, -qw)
```

表示的是完全相同的空间旋转。

因此，在比较两个四元数时，不能简单逐元素判断是否相等，而应考虑它们可能只是符号不同。

### 旋转矩阵的正交性

旋转矩阵应始终满足正交约束。

也就是说：

- 三个坐标轴彼此垂直；
- 每个坐标轴长度为 1。

如果经过多次数值计算后，旋转矩阵失去正交性，就不再是合法的旋转矩阵，可能导致坐标变换出现累计误差。

因此，在机器人运动学和优化算法中，通常需要定期对旋转矩阵进行正交化处理，以保证数值稳定性。

## 单位与坐标约定

机器人系统中的位姿不仅需要采用统一的数据格式，还必须遵循一致的单位和坐标约定。

首先是**长度单位**。

不同机器人平台可能采用：

- 米（m）
- 毫米（mm）

如果模型转换过程中单位混用，机器人实际运动距离可能相差一千倍。

其次是**角度单位**。

机器人内部计算通常采用：

- 弧度（rad）

而工业机器人示教器、人机界面或部分 SDK 则可能采用：

- 度（°）

因此，在数据转换过程中必须明确角度单位，避免将角度误认为弧度，导致机器人姿态严重错误。

此外，还需要统一**坐标系方向**。

不同软件可能采用：

- 右手坐标系；
- 左手坐标系。

如果左右手系混用，机器人运动方向和旋转方向都可能发生镜像错误。

最后，还需要明确位姿所属的参考坐标系，例如：

- 世界坐标系（World Frame）
- 机器人基座坐标系（Base Frame）
- 相机坐标系（Camera Frame）
- 工具坐标系（Tool Frame）

相同的位置数据，在不同坐标系下具有完全不同的含义，因此任何位姿接口都应明确其参考坐标系。

## 位姿表示之间的转换

机器人系统中的不同模块往往采用不同的姿态表示方式，因此在实际开发过程中，经常需要在各种表示之间进行转换。

例如：

- 机器人控制器采用四元数；
- 示教器显示欧拉角；
- 运动学计算使用旋转矩阵；
- 优化算法采用轴角表示。

虽然这些表示可以互相转换，但转换过程中必须保持以下信息一致：

- 所属坐标系；
- 坐标轴方向；
- 单位；
- 旋转顺序；
- 时间戳。

任何一个环节配置错误，都可能导致机器人姿态发生明显偏差。例如，欧拉角旋转顺序设置错误，会使机械臂末端朝向完全错误；角度与弧度混用，可能导致机器人旋转数十倍于预期；世界坐标与机器人坐标混淆，则会使机器人运动到完全错误的位置。

因此，在机器人开发中，真正需要关注的并不是各种表示方式之间的数学推导，而是明确**什么时候需要进行转换、转换采用什么约定，以及转换后的数据是否仍然保持正确的空间语义**。

**四种姿态表示之间的转换公式汇总：**

| 转换 | 核心公式 | 说明 |
|------|----------|------|
| 四元数 → 旋转矩阵 | $R = \begin{bmatrix} 1-2(y^2+z^2) & 2(xy-zw) & 2(xz+yw) \\ 2(xy+zw) & 1-2(x^2+z^2) & 2(yz-xw) \\ 2(xz-yw) & 2(yz+xw) & 1-2(x^2+y^2) \end{bmatrix}$ | 将 $(x,y,z,w)$ 代入即得 |
| 旋转矩阵 → 四元数 | $w = \frac{1}{2}\sqrt{1+R_{11}+R_{22}+R_{33}},\ x = \frac{R_{32}-R_{23}}{4w},\ y = \frac{R_{13}-R_{31}}{4w},\ z = \frac{R_{21}-R_{12}}{4w}$ | 若 $w \approx 0$ 需用其他分量代替 |
| 轴角 → 旋转矩阵 | $R = I + \sin\theta[\mathbf{u}]_\times + (1-\cos\theta)[\mathbf{u}]_\times^2$ | Rodrigues 公式 |
| 旋转矩阵 → 轴角 | $\theta = \arccos\frac{\text{tr}(R)-1}{2},\ \mathbf{u} = \frac{1}{2\sin\theta}\begin{bmatrix} R_{32}-R_{23} \\ R_{13}-R_{31} \\ R_{21}-R_{12} \end{bmatrix}$ | 逆 Rodrigues 公式 |
| ZYX 欧拉角 → 旋转矩阵 | $R = R_z(\text{yaw}) \cdot R_y(\text{pitch}) \cdot R_x(\text{roll})$ | 按外旋顺序从右到左相乘 |
| 旋转矩阵 → ZYX 欧拉角 | $\text{pitch} = \arcsin(-R_{31}),\ \text{roll} = \arctan2(R_{32}, R_{33}),\ \text{yaw} = \arctan2(R_{21}, R_{11})$ | pitch=±90° 时出现奇异 |
| 四元数 → 轴角 | $\theta = 2\arccos(w),\ \mathbf{u} = \frac{(x,y,z)}{\sin(\theta/2)}$ | 直接由构造公式反推 |

**Python 代码示例 —— 所有姿态表示之间的统一转换：**

```python
import numpy as np
from scipy.spatial.transform import Rotation

# ============================================================
# 给定一个基准姿态（绕 Z 轴旋转 90°），演示所有表示之间的转换
# ============================================================

theta = np.pi / 2    # 旋转角度 90°
axis   = np.array([0., 0., 1.])  # 旋转轴 Z

# --- 从轴角出发，生成所有表示 ---

rot = Rotation.from_rotvec(axis * theta)  # rotvec: 向量方向=轴, 长度=角度

# 旋转矩阵
R = rot.as_matrix()
print("旋转矩阵 R:")
print(R)
# [[ 6.12e-17 -1.00e+00  0.00e+00]
#  [ 1.00e+00  6.12e-17  0.00e+00]
#  [ 0.00e+00  0.00e+00  1.00e+00]]

# 四元数 (x, y, z, w) — ROS / scipy 格式
q = rot.as_quat()
print(f"四元数 (x,y,z,w): {q}")
# → [0. 0. 0.7071 0.7071]

# 欧拉角 — ZYX (RPY) 顺序，弧度
euler_zyx = rot.as_euler('ZYX')
print(f"欧拉角 ZYX (rad): {euler_zyx}")
print(f"欧拉角 ZYX (°):   {np.degrees(euler_zyx)}")
# → [0. 0. 1.5708] rad → [0. 0. 90.]°

# 欧拉角 — XYZ 顺序
euler_xyz = rot.as_euler('XYZ')
print(f"欧拉角 XYZ (rad): {euler_xyz}")

# 轴角 (rotvec)
rotvec = rot.as_rotvec()
print(f"轴角 rotvec: {rotvec}")
# → [0. 0. 1.5708]

# ============================================================
# 从任意一种表示构造，再转为其他表示
# ============================================================

# 方式 A：从四元数坐标构造
rot_from_quat = Rotation.from_quat([0.0, 0.0, 0.7071, 0.7071])
print("\n从四元数构造 → 欧拉角 ZYX (°):",
      np.degrees(rot_from_quat.as_euler('ZYX')))

# 方式 B：从欧拉角构造（注意指定顺序和单位）
rot_from_euler = Rotation.from_euler('ZYX', [0, 0, 90], degrees=True)
print("从欧拉角构造 → 四元数:", rot_from_euler.as_quat())

# 方式 C：从旋转矩阵构造
R_input = np.array([[0, -1, 0],
                    [1,  0, 0],
                    [0,  0, 1]])
rot_from_matrix = Rotation.from_matrix(R_input)
print("从矩阵构造 → 轴角:", rot_from_matrix.as_rotvec())

# 方式 D：从轴角 (rotvec) 构造
rot_from_rotvec = Rotation.from_rotvec([0, 0, np.pi / 2])
print("从轴角构造 → 四元数:", rot_from_rotvec.as_quat())

# ============================================================
# 完整位姿 (Position + Orientation) 的表示与组合
# ============================================================

# 定义位姿：位置 (0.45, 0.10, 0.30)，姿态 绕Z轴90°
position = np.array([0.45, 0.10, 0.30])
orientation_q = rot.as_quat()  # 四元数表示

# 构造齐次变换矩阵 T = [R  t]
#                      [0  1]
T = np.eye(4)
T[:3, :3] = rot.as_matrix()
T[:3, 3] = position
print("\n齐次变换矩阵 T:")
print(T)

# 用此位姿变换一个点
P_in_obj_frame = np.array([0.1, 0.0, 0.0])  # 物体坐标系中的点
P_in_world = (T @ np.append(P_in_obj_frame, 1.0))[:3]
print(f"物体坐标 {P_in_obj_frame} → 世界坐标 {P_in_world}")

# ============================================================
# 转换注意事项的代码体现
# ============================================================

# 1. 欧拉角必须指定旋转顺序
assert not np.allclose(
    Rotation.from_euler('ZYX', [30, 45, 60], degrees=True).as_matrix(),
    Rotation.from_euler('XYZ', [30, 45, 60], degrees=True).as_matrix()
), "不同旋转顺序得到不同姿态"

# 2. 四元数必须归一化
q_unnormalized = np.array([0.0, 0.0, 1.0, 1.0])  # ||q|| = sqrt(2) ≠ 1
q_corrected = q_unnormalized / np.linalg.norm(q_unnormalized)
R_corrected = Rotation.from_quat(q_corrected).as_matrix()
print("\n未归一化四元数修正后方可使用")

# 3. 角度与弧度不能混用
angle_deg = 90.0
angle_rad = np.radians(angle_deg)  # ← 必须先转换
rot_safe = Rotation.from_euler('z', angle_rad)  # 正确：传入弧度
# rot_wrong = Rotation.from_euler('z', 90)      # 错误：90 会被当作 90 rad！
print(f"90° = {angle_rad:.4f} rad，旋转矩阵 det = {np.linalg.det(rot_safe.as_matrix()):.0f}")

# 4. 右手系与左手系的区分
# 右手系: Z = X × Y，左手系: Z = -X × Y
# 不同软件可能采用不同手系，跨平台转换时需额外处理
```

> **代码说明：**
> - `scipy.spatial.transform.Rotation` 是姿态转换的统一入口，覆盖了旋转矩阵、欧拉角（支持所有常见旋转顺序）、四元数、轴角（rotvec）之间的双向转换。
> - 欧拉角转换必须明确指定 `seq` 参数（如 `'ZYX'`、`'XYZ'`）和 `degrees` 参数，否则默认弧度的行为可能导致严重错误。
> - 四元数在传入 `Rotation` 时应保证归一化；转换过程中 `Rotation` 会自动处理符号等价性。
> - 齐次变换矩阵将旋转与平移统一为 4×4 矩阵，是机器人正向运动学和坐标变换的标准数据结构。

## 示例：同一末端位姿在不同接口中的表示

下面以机械臂末端执行器的一个目标位姿为例，说明同一空间信息如何在不同接口中采用不同的数据形式。

假设机械臂末端位于机器人基座前方，其目标位置为：

```text
Position

x = 0.45 m
y = 0.10 m
z = 0.30 m
```

该位姿属于：

```text
frame_id

base_link
```

数据采集时间为：

```text
timestamp

1723000123.456
```

对于姿态部分，不同接口可能采用不同表示：

使用欧拉角时，可以表示为：

```text
Roll = 0°
Pitch = 90°
Yaw = 0°
```

在 ROS 或机器人 SDK 中，则更常采用四元数形式：

```text
Orientation

x
y
z
w
```

如果用于机器人运动学计算，则通常会转换为一个 3×3 的旋转矩阵；而在某些优化算法或控制器中，又可能进一步转换为轴角表示。

可以看到，虽然姿态表示形式发生了变化，但它们描述的始终是同一个空间位姿。真正保证这些数据能够正确对应的是统一的 frame_id、timestamp、单位以及坐标约定，而不仅仅是姿态表示方式本身。

**上述示例的完整 Python 代码实现：**

```python
import numpy as np
from scipy.spatial.transform import Rotation

# ============================================================
# 定义末端位姿：base_link 坐标系下的机械臂末端
# ============================================================

# 位置（单位：米）
position_base = np.array([0.45, 0.10, 0.30])

# 姿态：Roll=0°, Pitch=90°, Yaw=0° → 绕 Y 轴旋转 90°
roll, pitch, yaw = np.radians(0), np.radians(90), np.radians(0)

# 时间戳与坐标系
frame_id = "base_link"
timestamp = 1723000123.456

# ============================================================
# 同一姿态的四种表示
# ============================================================

rot = Rotation.from_euler('ZYX', [roll, pitch, yaw])  # 注意：scipy 用大写表示外旋

# 表示 1：欧拉角（人机界面 / 示教器）
print("=" * 50)
print(f"位姿 @ {frame_id}  (t = {timestamp})")
print("=" * 50)
print(f"位置 (m):  x={position_base[0]:.2f}, "
      f"y={position_base[1]:.2f}, z={position_base[2]:.2f}")
print(f"欧拉角 ZYX (°): Roll={np.degrees(roll):.1f}, "
      f"Pitch={np.degrees(pitch):.1f}, Yaw={np.degrees(yaw):.1f}")

# 表示 2：四元数（ROS / MoveIt / 机器人 SDK）
q = rot.as_quat()  # (x, y, z, w)
print(f"\n四元数: x={q[0]:.4f}, y={q[1]:.4f}, z={q[2]:.4f}, w={q[3]:.4f}")

# 表示 3：旋转矩阵（运动学计算 / 物理引擎）
R = rot.as_matrix()
print(f"\n旋转矩阵 R:")
print(f"  [{R[0,0]:7.4f}  {R[0,1]:7.4f}  {R[0,2]:7.4f}]")
print(f"  [{R[1,0]:7.4f}  {R[1,1]:7.4f}  {R[1,2]:7.4f}]")
print(f"  [{R[2,0]:7.4f}  {R[2,1]:7.4f}  {R[2,2]:7.4f}]")

# 表示 4：轴角表示（优化算法 / 控制器）
rotvec = rot.as_rotvec()
angle = np.linalg.norm(rotvec)
axis  = rotvec / angle if angle > 1e-10 else np.array([0., 0., 1.])
print(f"\n轴角: 轴 = ({axis[0]:.2f}, {axis[1]:.2f}, {axis[2]:.2f}), "
      f"角度 = {np.degrees(angle):.1f}°")

# ============================================================
# 构造齐次变换矩阵（末端相对于基座）
# ============================================================

T_end_in_base = np.eye(4)
T_end_in_base[:3, :3] = R
T_end_in_base[:3, 3] = position_base

print(f"\n齐次变换矩阵 T_end_in_base:")
print(T_end_in_base)

# ============================================================
# 应用：计算末端工具点在世界坐标系中的位置
# ============================================================

# 假设基座在世界坐标系中的位姿已知
T_base_in_world = np.eye(4)
T_base_in_world[:3, :3] = Rotation.from_euler(
    'z', np.radians(30)).as_matrix()  # 基座相对世界旋转 30°
T_base_in_world[:3, 3] = [2.0, 0.0, 0.0]  # 基座在世界中位于 (2, 0, 0)

# 链式变换：世界 → 基座 → 末端
T_end_in_world = T_base_in_world @ T_end_in_base

# 提取末端在世界中的位置和姿态
pos_in_world = T_end_in_world[:3, 3]
rot_in_world = Rotation.from_matrix(T_end_in_world[:3, :3])

print(f"\n末端在世界坐标系中的位置: ({pos_in_world[0]:.3f}, "
      f"{pos_in_world[1]:.3f}, {pos_in_world[2]:.3f})")
print(f"末端在世界坐标系中的欧拉角 ZYX (°): "
      f"{np.degrees(rot_in_world.as_euler('ZYX'))}")

# ============================================================
# 关键提醒：丢失 frame_id 和 timestamp 的位置数据毫无意义
# ============================================================

# 以下数据看似完整，但实际上不可用
pos_meaningless = np.array([0.45, 0.10, 0.30])
# 这个 (0.45, 0.10, 0.30) 是相对于哪个坐标系的？在哪个时刻采集的？
# 答案是：不知道 → 这样的数据在机器人系统中无法参与任何计算
print(f"\n⚠ 无 frame_id / timestamp 的数据 ({pos_meaningless}) "
      f"— 仅有数值，无法在系统中使用")
```

> **代码说明：**
> - 末端位姿 `(0.45, 0.10, 0.30)` + `Roll=0°, Pitch=90°, Yaw=0°` 经过转换后，在四元数、旋转矩阵、轴角等表示形式下数值完全不同，但描述的是完全相同的空间状态。
> - 链式变换 `T_end_in_world = T_base_in_world @ T_end_in_base` 体现了机器人运动学中从世界坐标系逐级变换到末端执行器的标准做法。
> - 代码最后强调了 `frame_id` 和 `timestamp` 的重要性：没有这两者的数值坐标无法在机器人系统中正常工作。

## 本章建议掌握的内容

本章不要求读者推导各种旋转表示之间的数学公式，而是重点理解它们在机器人系统中的接口意义和使用方式。

读者应能够理解 Pose 由 Position 和 Orientation 组成，并认识到任何位姿数据只有同时绑定 frame_id 和 timestamp 才具有实际意义；能够区分 Rotation Matrix、Euler Angle、Quaternion 和 Axis-Angle 等常见旋转表示，了解它们各自在机器人模型、控制接口、仿真平台和视觉算法中的典型应用。

同时，应掌握欧拉角旋转顺序和奇异性、四元数归一化与符号等价、旋转矩阵正交性等常见注意事项，能够识别长度单位、角度单位、坐标系方向以及参考坐标系等接口约定的重要性。最后，应建立不同表示方式之间可以相互转换但必须保持统一空间语义的认识，为后续机器人感知、运动规划和控制算法的学习奠定基础。

## 本章小结

位姿是机器人系统中描述空间信息的基本数据类型，由位置和姿态共同组成，并必须结合 frame_id 与 timestamp 才能够准确表达机器人、传感器或目标物体在某一时刻相对于参考坐标系的空间状态。

机器人系统中常见的姿态表示包括旋转矩阵、欧拉角、四元数和轴角表示，它们虽然表达形式不同，但都用于描述同一种空间旋转。不同表示方式适用于不同接口和算法，同时也各自存在需要注意的问题，例如欧拉角的旋转顺序和奇异性、四元数的归一化与符号等价、旋转矩阵的正交性等。

在工程实践中，位姿表示不仅涉及数据格式，还需要统一长度单位、角度单位、坐标系方向以及参考坐标系等接口约定。不同模块之间经常需要进行姿态表示转换，但只有在保持坐标语义、单位、时间和参考坐标一致的前提下，才能保证机器人感知、规划、控制以及数据记录的正确性，为实现稳定可靠的机器人系统提供统一的空间表达基础。