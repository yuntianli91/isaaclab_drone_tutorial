"""把速度与绝对航向指令转换成推力和期望姿态。"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from isaaclab.utils.math import matrix_from_quat, quat_from_matrix


@dataclass(frozen=True)
class VelocityYawControllerCfg:
  """速度与航向控制器参数。"""

  velocity_kp: tuple[float, float, float] = (  # 速度比例增益 (1/s)。
    3.0,
    3.0,
    4.5,
  )
  max_tilt_rad: float = 0.6                    # 最大倾角 (rad)。
  thrust_to_weight: float = 1.9                # 最大推重比。


class VelocityYawController:
  """批量计算 collective thrust 和 WXYZ 期望姿态。"""

  # ===== __init__ =========================================================== #
  def __init__(self, num_envs: int, device: str, robot_mass: float,
               gravity_magnitude: float,
               cfg: VelocityYawControllerCfg | None = None) -> None:
    """初始化物理参数和速度增益。

    Args:
      num_envs: 并行环境数量。
      device: Torch 计算设备。
      robot_mass: UAV 整机质量 (kg)。
      gravity_magnitude: 重力加速度幅值 (m/s²)。
      cfg: 可选的控制器配置。
    """
    self.cfg = cfg or VelocityYawControllerCfg()
    self.num_envs = num_envs
    self.device = torch.device(device)
    self.robot_mass = robot_mass
    self.robot_weight = robot_mass * gravity_magnitude
    self.velocity_kp = torch.tensor(
      self.cfg.velocity_kp, device=self.device
    )
    self.max_tilt = torch.tensor(
      self.cfg.max_tilt_rad, device=self.device
    )

  # ===== compute ============================================================ #
  def compute(self, desired_velocity_w: torch.Tensor,
              desired_yaw: torch.Tensor, current_velocity_w: torch.Tensor,
              current_quaternion_wxyz: torch.Tensor,
              ) -> tuple[torch.Tensor, torch.Tensor]:
    """计算推力和期望姿态。

    Args:
      desired_velocity_w: world 坐标系期望速度 (m/s)，形状为 ``(N, 3)``。
      desired_yaw: world 坐标系绝对期望航向 (rad)，形状为 ``(N,)``。
      current_velocity_w: world 坐标系当前速度 (m/s)，形状为 ``(N, 3)``。
      current_quaternion_wxyz: 当前 WXYZ 姿态，形状为 ``(N, 4)``。

    Returns:
      collective thrust (N) 和期望 WXYZ 姿态组成的二元组。
    """
    expected_vector = (self.num_envs, 3)
    if desired_velocity_w.shape != expected_vector:
      raise ValueError("desired_velocity_w has an invalid shape.")
    if current_velocity_w.shape != expected_vector:
      raise ValueError("current_velocity_w has an invalid shape.")
    if desired_yaw.shape != (self.num_envs,):
      raise ValueError("desired_yaw has an invalid shape.")
    if current_quaternion_wxyz.shape != (self.num_envs, 4):
      raise ValueError("current_quaternion_wxyz has an invalid shape.")

    velocity_error = desired_velocity_w - current_velocity_w
    desired_acceleration = self.velocity_kp * velocity_error
    desired_force_w = self.robot_mass * desired_acceleration
    desired_force_w[:, 2] += self.robot_weight

    vertical_force = desired_force_w[:, 2].clamp_min(
      0.05 * self.robot_weight
    )
    horizontal_force = desired_force_w[:, 0:2]
    horizontal_limit = vertical_force * torch.tan(self.max_tilt)
    horizontal_norm = torch.linalg.vector_norm(
      horizontal_force, dim=-1
    ).clamp_min(1.0e-6)
    horizontal_scale = torch.minimum(
      torch.ones_like(horizontal_norm),
      horizontal_limit / horizontal_norm,
    )
    desired_force_w[:, 0:2] = (
      horizontal_force * horizontal_scale.unsqueeze(-1)
    )

    body_z_desired = torch.nn.functional.normalize(desired_force_w, dim=-1)
    heading_x = torch.stack(
      (
        torch.cos(desired_yaw),
        torch.sin(desired_yaw),
        torch.zeros_like(desired_yaw),
      ),
      dim=-1,
    )
    body_y_desired = torch.nn.functional.normalize(
      torch.linalg.cross(body_z_desired, heading_x, dim=-1), dim=-1
    )
    body_x_desired = torch.linalg.cross(
      body_y_desired, body_z_desired, dim=-1
    )
    rotation_desired = torch.stack(
      (body_x_desired, body_y_desired, body_z_desired), dim=-1
    )
    desired_quaternion_wxyz = quat_from_matrix(rotation_desired)

    current_rotation = matrix_from_quat(current_quaternion_wxyz)
    current_body_z_w = current_rotation[:, :, 2]
    collective_thrust = torch.sum(
      desired_force_w * current_body_z_w, dim=-1
    ).clamp(0.0, self.cfg.thrust_to_weight * self.robot_weight)
    return collective_thrust, desired_quaternion_wxyz
