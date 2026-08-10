"""面向 Crazyflie 归一化 wrench 动作的批量串级 PID baseline。"""

from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class CascadedPIDControllerCfg:
  """使用 SI 单位表示的控制器参数。

  外环控制 world-frame 位置，内环控制 body 姿态和角速度。输出遵循
  Tutorial 1 的归一化总推力与三轴力矩接口。
  """

  position_kp: tuple[float, float, float] = (4.0, 4.0, 8.0)     # 位置比例增益。
  position_ki: tuple[float, float, float] = (0.0, 0.0, 0.0)     # 位置积分增益。
  position_kd: tuple[float, float, float] = (3.0, 3.0, 4.5)     # 位置微分增益。
  attitude_kp: tuple[float, float, float] = (0.08, 0.08, 0.03)  # 姿态比例增益。
  attitude_ki: tuple[float, float, float] = (0.0, 0.0, 0.0)     # 姿态积分增益。
  attitude_kd: tuple[float, float, float] = (
    (0.003, 0.003, 0.001)                                       # 姿态微分增益。
  )
  position_integral_limit: float = 0.5                          # 位置积分限幅。
  attitude_integral_limit: float = 0.3                          # 姿态积分限幅。
  max_tilt_rad: float = 0.6                                     # 倾角 (rad)。
  thrust_to_weight: float = 1.9                                 # 最大推重比。
  moment_scale: float = 0.01                                    # 力矩 (N·m)。


# ===== _quaternion_wxyz_to_matrix =========================================== #
def _quaternion_wxyz_to_matrix(quaternion: torch.Tensor) -> torch.Tensor:
  """将一批归一化 WXYZ 四元数转换为旋转矩阵。

  Args:
    quaternion: 形状为 ``(num_envs, 4)`` 的 WXYZ 四元数。

  Returns:
    形状为 ``(num_envs, 3, 3)`` 的旋转矩阵。
  """
  quaternion = torch.nn.functional.normalize(quaternion, dim=-1)
  w, x, y, z = quaternion.unbind(dim=-1)
  two = 2.0
  return torch.stack(
    (
      1.0 - two * (y * y + z * z),
      two * (x * y - z * w),
      two * (x * z + y * w),
      two * (x * y + z * w),
      1.0 - two * (x * x + z * z),
      two * (y * z - x * w),
      two * (x * z - y * w),
      two * (y * z + x * w),
      1.0 - two * (x * x + y * y),
    ),
    dim=-1,
  ).reshape(-1, 3, 3)


class CascadedPIDController:
  """位于环境外部的 Torch 批量位置和姿态控制器。"""

  # ===== __init__ =========================================================== #
  def __init__(self, num_envs: int, device: str, control_dt: float,
               robot_mass: float, gravity_magnitude: float,
               cfg: CascadedPIDControllerCfg | None = None) -> None:
    """初始化控制参数和每个环境独立的积分状态。

    Args:
      num_envs: 并行环境数量。
      device: Torch 计算设备。
      control_dt: 控制周期 (s)。
      robot_mass: 无人机总质量 (kg)。
      gravity_magnitude: 重力加速度幅值 (m/s²)。
      cfg: 可选的 PID 参数配置。
    """
    self.cfg = cfg or CascadedPIDControllerCfg()
    self.num_envs = num_envs
    self.device = torch.device(device)
    self.control_dt = control_dt
    self.robot_mass = robot_mass
    self.gravity_magnitude = gravity_magnitude
    self.robot_weight = robot_mass * gravity_magnitude

    self.position_kp = torch.tensor(
      self.cfg.position_kp, device=self.device
    )
    self.position_ki = torch.tensor(
      self.cfg.position_ki, device=self.device
    )
    self.position_kd = torch.tensor(
      self.cfg.position_kd, device=self.device
    )
    self.attitude_kp = torch.tensor(
      self.cfg.attitude_kp, device=self.device
    )
    self.attitude_ki = torch.tensor(
      self.cfg.attitude_ki, device=self.device
    )
    self.attitude_kd = torch.tensor(
      self.cfg.attitude_kd, device=self.device
    )

    self.position_error_integral = torch.zeros(
      num_envs, 3, device=self.device
    )
    self.attitude_error_integral = torch.zeros(
      num_envs, 3, device=self.device
    )

  # ===== reset ============================================================== #
  def reset(self, env_ids: torch.Tensor | None = None) -> None:
    """清空全部或指定环境的积分状态。

    Args:
      env_ids: 需要清空积分状态的环境索引；``None`` 表示全部环境。
    """
    if env_ids is None:
      env_ids = slice(None)
    self.position_error_integral[env_ids] = 0.0
    self.attitude_error_integral[env_ids] = 0.0

  # ===== compute ============================================================ #
  def compute(self, observation: torch.Tensor,
              target_position: torch.Tensor) -> torch.Tensor:
    """根据 Tutorial 1 的 13 维观测计算归一化动作。

    Args:
      observation: 位置、WXYZ 四元数、world 线速度和 body 角速度。
      target_position: 每个环境的局部目标位置 (m)。

    Returns:
      形状为 ``(num_envs, 4)`` 的归一化推力和三轴力矩。

    Raises:
      ValueError: 观测或目标位置的 batch shape 不符合接口约定。
    """
    if observation.shape != (self.num_envs, 13):
      raise ValueError(
        f"Expected observation shape {(self.num_envs, 13)}, got "
        f"{tuple(observation.shape)}"
      )
    if target_position.shape != (self.num_envs, 3):
      raise ValueError(
        f"Expected target shape {(self.num_envs, 3)}, got "
        f"{tuple(target_position.shape)}"
      )

    position = observation[:, 0:3]
    quaternion = observation[:, 3:7]
    linear_velocity_w = observation[:, 7:10]
    angular_velocity_b = observation[:, 10:13]

    position_error = target_position - position
    self.position_error_integral.add_(position_error * self.control_dt)
    self.position_error_integral.clamp_(
      -self.cfg.position_integral_limit, self.cfg.position_integral_limit
    )

    desired_acceleration = (
      self.position_kp * position_error
      + self.position_ki * self.position_error_integral
      - self.position_kd * linear_velocity_w
    )
    desired_force_w = self.robot_mass * desired_acceleration
    desired_force_w[:, 2] += self.robot_weight

    # 在保留竖直分量的同时，通过最大倾角限制水平合力。
    vertical_force = desired_force_w[:, 2].clamp_min(
      0.05 * self.robot_weight
    )
    horizontal_force = desired_force_w[:, :2]
    horizontal_limit = vertical_force * torch.tan(
      torch.tensor(self.cfg.max_tilt_rad, device=self.device)
    )
    horizontal_norm = torch.linalg.vector_norm(
      horizontal_force, dim=-1
    ).clamp_min(1.0e-6)
    horizontal_scale = torch.minimum(
      torch.ones_like(horizontal_norm), horizontal_limit / horizontal_norm
    )
    desired_force_w[:, :2] = horizontal_force * horizontal_scale.unsqueeze(
      -1
    )

    body_z_desired = torch.nn.functional.normalize(desired_force_w, dim=-1)
    heading_x = torch.zeros_like(body_z_desired)
    heading_x[:, 0] = 1.0  # 固定期望 yaw 为 0。
    body_y_desired = torch.nn.functional.normalize(
      torch.linalg.cross(body_z_desired, heading_x), dim=-1
    )
    body_x_desired = torch.linalg.cross(body_y_desired, body_z_desired)
    rotation_desired = torch.stack(
      (body_x_desired, body_y_desired, body_z_desired), dim=-1
    )

    rotation = _quaternion_wxyz_to_matrix(quaternion)
    attitude_matrix_error = (
      rotation_desired.transpose(1, 2) @ rotation
      - rotation.transpose(1, 2) @ rotation_desired
    )
    attitude_error = 0.5 * torch.stack(
      (
        attitude_matrix_error[:, 2, 1],
        attitude_matrix_error[:, 0, 2],
        attitude_matrix_error[:, 1, 0],
      ),
      dim=-1,
    )
    self.attitude_error_integral.add_(attitude_error * self.control_dt)
    self.attitude_error_integral.clamp_(
      -self.cfg.attitude_integral_limit, self.cfg.attitude_integral_limit
    )

    moment = (
      -self.attitude_kp * attitude_error
      - self.attitude_ki * self.attitude_error_integral
      - self.attitude_kd * angular_velocity_b
    )

    current_body_z_w = rotation[:, :, 2]
    collective_thrust = torch.sum(
      desired_force_w * current_body_z_w, dim=-1
    ).clamp(0.0, self.cfg.thrust_to_weight * self.robot_weight)
    normalized_thrust = (
      2.0
      * collective_thrust
      / (self.cfg.thrust_to_weight * self.robot_weight)
      - 1.0
    )
    normalized_moment = moment / self.cfg.moment_scale
    return torch.cat(
      (normalized_thrust.unsqueeze(-1), normalized_moment), dim=-1
    ).clamp(-1.0, 1.0)
