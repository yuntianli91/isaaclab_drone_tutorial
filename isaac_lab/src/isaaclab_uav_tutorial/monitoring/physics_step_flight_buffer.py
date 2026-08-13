"""在 GPU 上缓存一个 environment 的 physics-rate 飞行数据。"""

from __future__ import annotations

import torch

from isaaclab_uav_tutorial.utils import (
  matrix_from_quaternion,
  quaternion_from_matrix,
)

from .flight_schema import FLIGHT_SAMPLE_WIDTH


class PhysicsStepFlightBuffer:
  """采集 physics step 数据并执行完整的 ``W → E`` 坐标变换。"""

  # ===== __init__ =========================================================== #
  def __init__(self, env_id: int, capacity: int, physics_dt: float,
               origin_we: torch.Tensor,
               rotation_ew: torch.Tensor) -> None:
    """创建固定容量的单环境 GPU tensor buffer。

    Args:
      env_id: 从批量仿真数据中选取的 environment 索引。
      capacity: 每次批量导出的最大 physics sample 数量。
      physics_dt: 相邻 physics sample 的时间间隔 (s)。
      origin_we: `E` 系原点在 `W` 系的位置，形状为 ``(3,)``。
      rotation_ew: 将 `W` 系向量旋转到 `E` 系的矩阵，形状为
        ``(3, 3)``。

    Raises:
      ValueError: 索引、容量、周期或坐标变换形状不符合约定。
    """
    if env_id < 0 or capacity < 1 or physics_dt <= 0.0:
      raise ValueError("env_id, capacity, or physics_dt is invalid.")
    if origin_we.shape != (3,) or rotation_ew.shape != (3, 3):
      raise ValueError("origin_we or rotation_ew has an invalid shape.")

    self._env_id = env_id
    self._capacity = capacity
    self._physics_dt = physics_dt
    self._origin_we = origin_we.clone()
    self._rotation_ew = rotation_ew.clone()
    self._samples = torch.zeros(capacity, FLIGHT_SAMPLE_WIDTH,
                                device=origin_we.device)
    self._sample_count = 0
    self._total_sample_count = 0

  # ===== record ============================================================= #
  def record(self, position_w: torch.Tensor, quaternion_wb: torch.Tensor,
             linear_velocity_w: torch.Tensor,
             angular_velocity_b: torch.Tensor,
             desired_velocity_e: torch.Tensor, desired_yaw_e: torch.Tensor,
             collective_thrust: torch.Tensor,
             desired_quaternion_eb: torch.Tensor,
             body_torque_b: torch.Tensor) -> None:
    """缓存当前 physics interval 起点的状态、指令和控制输出。

    Args:
      position_w: `W` 系位置，形状为 ``(num_envs, 3)``。
      quaternion_wb: `B` 系相对于 `W` 系的 WXYZ 姿态，形状为
        ``(num_envs, 4)``。
      linear_velocity_w: `W` 系线速度，形状为 ``(num_envs, 3)``。
      angular_velocity_b: `B` 系角速度，形状为 ``(num_envs, 3)``。
      desired_velocity_e: `E` 系期望速度，形状为 ``(num_envs, 3)``。
      desired_yaw_e: `E` 系绝对期望航向，形状为 ``(num_envs,)``。
      collective_thrust: 沿 `B` 系推力轴的总推力，形状为
        ``(num_envs,)``。
      desired_quaternion_eb: `B` 系相对于 `E` 系的期望 WXYZ 姿态，
        形状为 ``(num_envs, 4)``。
      body_torque_b: `B` 系合力矩，形状为 ``(num_envs, 3)``。

    Raises:
      RuntimeError: 尚未导出上一批数据，导致 buffer 容量不足。
    """
    if self._sample_count >= self._capacity:
      raise RuntimeError("PhysicsStepFlightBuffer capacity was exceeded.")

    env_id = self._env_id
    position_e = self._rotation_ew @ (
      position_w[env_id] - self._origin_we
    )
    linear_velocity_e = self._rotation_ew @ linear_velocity_w[env_id]
    rotation_wb = matrix_from_quaternion(
      quaternion_wb[env_id].unsqueeze(0)
    )[0]
    rotation_eb = self._rotation_ew @ rotation_wb
    quaternion_eb = quaternion_from_matrix(rotation_eb.unsqueeze(0))[0]
    values = torch.cat((
      position_e, quaternion_eb, linear_velocity_e,
      angular_velocity_b[env_id], desired_velocity_e[env_id],
      desired_yaw_e[env_id].reshape(1),
      collective_thrust[env_id].reshape(1),
      desired_quaternion_eb[env_id], body_torque_b[env_id],
    ))

    row = self._samples[self._sample_count]
    row[0] = self._total_sample_count * self._physics_dt
    row[1:].copy_(values)
    self._sample_count += 1
    self._total_sample_count += 1

  # ===== consume ============================================================ #
  def consume(self) -> torch.Tensor:
    """返回当前批次的副本并清空待导出样本。

    Returns:
      形状为 ``(num_samples, FLIGHT_SAMPLE_WIDTH)`` 的 GPU tensor。
    """
    samples = self._samples[:self._sample_count].clone()
    self._sample_count = 0
    return samples

  # ===== clear ============================================================== #
  def clear(self) -> None:
    """丢弃尚未导出的样本，但保持连续的仿真时间。"""
    self._sample_count = 0
