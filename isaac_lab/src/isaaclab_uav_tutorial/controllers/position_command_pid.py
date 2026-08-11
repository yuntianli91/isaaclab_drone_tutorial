"""把位置指令转换成高层速度和绝对航向动作的批量基线。"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

import torch


@dataclass(frozen=True)
class PositionCommandPIDCfg:
  """位置指令控制器参数。"""

  position_kp: tuple[float, float, float] = (  # 位置比例增益 (1/s)。
    4.0 / 3.0,
    4.0 / 3.0,
    8.0 / 4.5,
  )
  position_ki: tuple[float, float, float] = (  # 位置积分增益 (1/s²)。
    0.0,
    0.0,
    0.0,
  )
  position_integral_limit: float = 0.5         # 位置积分限幅 (m·s)。


class PositionCommandPID:
  """作为 RL Planner baseline 的位置指令控制器。"""

  # ===== __init__ =========================================================== #
  def __init__(self, num_envs: int, device: str, control_dt: float,
               velocity_scale: Sequence[float],
               cfg: PositionCommandPIDCfg | None = None) -> None:
    """创建每个环境独立的积分状态。

    Args:
      num_envs: 并行环境数量。
      device: Torch 计算设备。
      control_dt: Planner 调用周期 (s)。
      velocity_scale: 三轴最大速度绝对值 (m/s)。
      cfg: 可选的控制器配置。
    """
    self.cfg = cfg or PositionCommandPIDCfg()
    self.num_envs = num_envs
    self.device = torch.device(device)
    self.control_dt = control_dt
    self.velocity_scale = torch.as_tensor(
      velocity_scale, dtype=torch.float32, device=self.device
    )
    if self.velocity_scale.shape != (3,) or torch.any(
      self.velocity_scale <= 0.0
    ):
      raise ValueError("velocity_scale must contain three positive values.")

    self.position_kp = torch.tensor(
      self.cfg.position_kp, device=self.device
    )
    self.position_ki = torch.tensor(
      self.cfg.position_ki, device=self.device
    )
    self.position_error_integral = torch.zeros(
      num_envs, 3, device=self.device
    )

  # ===== reset ============================================================== #
  def reset(self, env_ids: Sequence[int] | slice | None = None) -> None:
    """清空全部或指定环境的位置误差积分。

    Args:
      env_ids: 需要清空的环境索引；``None`` 表示全部环境。
    """
    selected_envs = slice(None) if env_ids is None else env_ids
    self.position_error_integral[selected_envs] = 0.0

  # ===== compute ============================================================ #
  def compute(self, observation: torch.Tensor,
              target_position: torch.Tensor,
              target_yaw: torch.Tensor) -> torch.Tensor:
    """计算与未来 RL Policy 相同语义的归一化动作。

    Args:
      observation: 形状为 ``(num_envs, 13)`` 的 policy 观测。
      target_position: 形状为 ``(num_envs, 3)`` 的局部目标位置 (m)。
      target_yaw: 形状为 ``(num_envs,)`` 的绝对目标航向角 (rad)。

    Returns:
      形状为 ``(num_envs, 4)`` 的归一化
      ``[v_x, v_y, v_z, yaw]`` 动作。

    Raises:
      ValueError: 输入张量的 batch shape 不符合接口约定。
    """
    if observation.shape != (self.num_envs, 13):
      raise ValueError(
        f"Expected observation shape {(self.num_envs, 13)}, got "
        f"{tuple(observation.shape)}."
      )
    if target_position.shape != (self.num_envs, 3):
      raise ValueError(
        f"Expected target_position shape {(self.num_envs, 3)}, got "
        f"{tuple(target_position.shape)}."
      )
    if target_yaw.shape != (self.num_envs,):
      raise ValueError(
        f"Expected target_yaw shape {(self.num_envs,)}, got "
        f"{tuple(target_yaw.shape)}."
      )

    position_error = target_position - observation[:, 0:3]
    self.position_error_integral.add_(position_error * self.control_dt)
    self.position_error_integral.clamp_(
      -self.cfg.position_integral_limit,
      self.cfg.position_integral_limit,
    )
    desired_velocity_w = (
      self.position_kp * position_error
      + self.position_ki * self.position_error_integral
    )
    normalized_velocity = desired_velocity_w / self.velocity_scale
    wrapped_yaw = torch.atan2(torch.sin(target_yaw), torch.cos(target_yaw))
    normalized_yaw = wrapped_yaw / math.pi
    return torch.cat(
      (normalized_velocity, normalized_yaw.unsqueeze(-1)), dim=-1
    ).clamp(-1.0, 1.0)
