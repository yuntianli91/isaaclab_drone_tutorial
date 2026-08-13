"""把速度与绝对航向指令转换成推力和期望姿态。"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from isaaclab.utils.math import matrix_from_quat, quat_from_matrix


@dataclass(frozen=True)
class VelocityYawControllerCfg:
  """速度与航向控制器参数。"""

  velocity_kp: tuple[float, float, float]  # 速度比例增益 (1/s)。
  max_tilt_rad: float                      # 最大倾角 (rad)。
  thrust_to_weight: float                  # 最大推重比。


class VelocityYawController:
  """批量计算 collective thrust 和 WXYZ 期望姿态。"""

  # ===== __init__ =========================================================== #
  def __init__(self, num_envs: int, device: str, robot_mass: float,
               gravity_magnitude: float,
               cfg: VelocityYawControllerCfg) -> None:
    """初始化物理参数和速度增益。

    Args:
      num_envs: 并行环境数量。
      device: Torch 计算设备。
      robot_mass: UAV 整机质量 (kg)。
      gravity_magnitude: 重力加速度幅值 (m/s²)。
      cfg: 从项目配置构建的速度与航向控制器配置。
    """
    self.cfg = cfg
    self.num_envs = num_envs
    self.device = torch.device(device)
    self.robot_mass = robot_mass
    self.robot_weight = robot_mass * gravity_magnitude
    self.velocity_kp = torch.tensor(self.cfg.velocity_kp, device=self.device)
    self.max_tilt = torch.tensor(self.cfg.max_tilt_rad, device=self.device)

  # ===== compute ============================================================ #
  def compute(self, desired_velocity_e: torch.Tensor,
              desired_yaw_e: torch.Tensor,
              current_velocity_e: torch.Tensor,
              current_quaternion_eb: torch.Tensor
              ) -> tuple[torch.Tensor, torch.Tensor]:
    """计算推力和期望姿态。

    Args:
      desired_velocity_e: `E` 系期望速度 (m/s)，形状为
        ``(N, 3)``。
      desired_yaw_e: `E` 系绝对期望航向 (rad)，形状为
        ``(N,)``。
      current_velocity_e: `E` 系当前速度 (m/s)，形状为
        ``(N, 3)``。
      current_quaternion_eb: `B` 系相对于 `E` 系的当前 WXYZ 姿态，
        形状为 ``(N, 4)``。

    Returns:
      collective thrust (N) 和期望 WXYZ 姿态组成的二元组。
    """
    expected_vector = (self.num_envs, 3)
    if desired_velocity_e.shape != expected_vector:
      raise ValueError("desired_velocity_e has an invalid shape.")
    if current_velocity_e.shape != expected_vector:
      raise ValueError("current_velocity_e has an invalid shape.")
    if desired_yaw_e.shape != (self.num_envs,):
      raise ValueError("desired_yaw_e has an invalid shape.")
    if current_quaternion_eb.shape != (self.num_envs, 4):
      raise ValueError("current_quaternion_eb has an invalid shape.")

    velocity_error = desired_velocity_e - current_velocity_e
    desired_acceleration = self.velocity_kp * velocity_error
    desired_force_e = self.robot_mass * desired_acceleration
    desired_force_e[:, 2] += self.robot_weight

    vertical_force = desired_force_e[:, 2].clamp_min(0.05 * self.robot_weight)
    horizontal_force = desired_force_e[:, 0:2]
    horizontal_limit = vertical_force * torch.tan(self.max_tilt)
    horizontal_norm = torch.linalg.vector_norm(horizontal_force, dim=-1)
    horizontal_norm = horizontal_norm.clamp_min(1.0e-6)
    horizontal_scale = torch.minimum(torch.ones_like(horizontal_norm),
                                     horizontal_limit / horizontal_norm)
    desired_force_e[:, 0:2] = (
      horizontal_force * horizontal_scale.unsqueeze(-1)
    )

    body_z_desired = torch.nn.functional.normalize(desired_force_e, dim=-1)
    heading_x = torch.stack((torch.cos(desired_yaw_e),
                             torch.sin(desired_yaw_e),
                             torch.zeros_like(desired_yaw_e)), dim=-1)
    body_y_input = torch.linalg.cross(body_z_desired, heading_x, dim=-1)
    body_y_desired = torch.nn.functional.normalize(body_y_input, dim=-1)
    body_x_desired = torch.linalg.cross(body_y_desired, body_z_desired,
                                        dim=-1)
    rotation_desired = torch.stack((body_x_desired, body_y_desired,
                                    body_z_desired), dim=-1)
    desired_quaternion_eb = quat_from_matrix(rotation_desired)

    current_rotation_eb = matrix_from_quat(current_quaternion_eb)
    current_body_z_e = current_rotation_eb[:, :, 2]
    collective_thrust = torch.sum(desired_force_e * current_body_z_e,
                                  dim=-1)
    max_thrust = self.cfg.thrust_to_weight * self.robot_weight
    collective_thrust = collective_thrust.clamp(0.0, max_thrust)
    return collective_thrust, desired_quaternion_eb
