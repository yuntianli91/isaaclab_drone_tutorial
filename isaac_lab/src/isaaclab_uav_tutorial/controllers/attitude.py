"""把推力和期望姿态转换成 UAV 机体系 body wrench。"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import torch
from isaaclab.utils.math import matrix_from_quat


@dataclass(frozen=True)
class AttitudeControllerCfg:
  """姿态控制器参数。"""

  attitude_kp: tuple[float, float, float] = (  # 姿态比例增益 (N·m)。
    0.08,
    0.08,
    0.03,
  )
  attitude_ki: tuple[float, float, float] = (  # 姿态积分增益 (N·m/s)。
    0.0,
    0.0,
    0.0,
  )
  attitude_kd: tuple[float, float, float] = (  # 角速度增益 (N·m·s)。
    0.003,
    0.003,
    0.001,
  )
  attitude_integral_limit: float = 0.3         # 姿态误差积分限幅 (s)。
  moment_scale: float = 0.01                   # 三轴最大合力矩 (N·m)。


class AttitudeController:
  """批量姿态控制器，输出机体系合力和合力矩。"""

  # ===== __init__ =========================================================== #
  def __init__(self, num_envs: int, device: str, control_dt: float,
               cfg: AttitudeControllerCfg | None = None) -> None:
    """初始化增益和每个环境独立的姿态积分状态。

    Args:
      num_envs: 并行环境数量。
      device: Torch 计算设备。
      control_dt: 姿态控制器调用周期 (s)。
      cfg: 可选的控制器配置。
    """
    self.cfg = cfg or AttitudeControllerCfg()
    self.num_envs = num_envs
    self.device = torch.device(device)
    self.control_dt = control_dt
    self.attitude_kp = torch.tensor(
      self.cfg.attitude_kp, device=self.device
    )
    self.attitude_ki = torch.tensor(
      self.cfg.attitude_ki, device=self.device
    )
    self.attitude_kd = torch.tensor(
      self.cfg.attitude_kd, device=self.device
    )
    self.attitude_error_integral = torch.zeros(
      num_envs, 3, device=self.device
    )

  # ===== reset ============================================================== #
  def reset(self, env_ids: Sequence[int] | slice | None = None) -> None:
    """清空全部或指定环境的姿态误差积分。

    Args:
      env_ids: 需要清空的环境索引；``None`` 表示全部环境。
    """
    selected_envs = slice(None) if env_ids is None else env_ids
    self.attitude_error_integral[selected_envs] = 0.0

  # ===== compute ============================================================ #
  def compute(self, collective_thrust: torch.Tensor,
              desired_quaternion_wxyz: torch.Tensor,
              current_quaternion_wxyz: torch.Tensor,
              current_angular_velocity_b: torch.Tensor,
              ) -> tuple[torch.Tensor, torch.Tensor]:
    """计算机体系合力与合力矩。

    Args:
      collective_thrust: 沿机体系 Z 轴的总推力 (N)，形状为 ``(N,)``。
      desired_quaternion_wxyz: 期望 WXYZ 姿态，形状为 ``(N, 4)``。
      current_quaternion_wxyz: 当前 WXYZ 姿态，形状为 ``(N, 4)``。
      current_angular_velocity_b: 当前机体系角速度，形状为 ``(N, 3)``。

    Returns:
      机体系合力 (N) 和机体系合力矩 (N·m) 组成的二元组。
    """
    rotation_desired = matrix_from_quat(desired_quaternion_wxyz)
    rotation = matrix_from_quat(current_quaternion_wxyz)
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
      -self.cfg.attitude_integral_limit,
      self.cfg.attitude_integral_limit,
    )
    torques_b = (
      -self.attitude_kp * attitude_error
      - self.attitude_ki * self.attitude_error_integral
      - self.attitude_kd * current_angular_velocity_b
    ).clamp(-self.cfg.moment_scale, self.cfg.moment_scale)
    forces_b = torch.zeros(self.num_envs, 3, device=self.device)
    forces_b[:, 2] = collective_thrust
    return forces_b, torques_b
