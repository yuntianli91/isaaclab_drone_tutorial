"""将机体系合力和合力矩施加到 UAV 刚体的辅助类。"""

from __future__ import annotations

from collections.abc import Sequence

import torch
from isaaclab.assets import Articulation


class BodyWrenchApplier:
  """管理永久 wrench buffer，并把它施加到唯一的 UAV 机体刚体。"""

  # ===== __init__ =========================================================== #
  def __init__(self, asset: Articulation, body_name: str) -> None:
    """解析目标刚体并创建批量 wrench buffer。

    Args:
      asset: 接收合力和合力矩的 UAV Articulation。
      body_name: 接收 wrench 的唯一刚体名称。

    Raises:
      ValueError: ``body_name`` 没有且仅匹配一个刚体。
    """
    self._asset = asset
    self._body_ids, body_names = asset.find_bodies(body_name)
    if len(self._body_ids) != 1:
      raise ValueError(
        f"Expected body_name={body_name!r} to match exactly one body; "
        f"matched {body_names}."
      )

    num_envs = asset.data.root_pos_w.shape[0]
    device = asset.device
    # WrenchComposer 的张量布局为 (并行环境数, 选中刚体数, XYZ)。
    self._forces_b = torch.zeros(num_envs, 1, 3, device=device)
    self._torques_b = torch.zeros_like(self._forces_b)

  # ===== apply ============================================================= #
  def apply(self, forces_b: torch.Tensor, torques_b: torch.Tensor) -> None:
    """缓存并施加机体系合力与合力矩。

    Args:
      forces_b: 形状为 ``(num_envs, 3)`` 的机体系合力 (N)。
      torques_b: 形状为 ``(num_envs, 3)`` 的机体系合力矩 (N·m)。

    Raises:
      ValueError: 输入张量形状与 wrench buffer 不一致。
    """
    expected_shape = (self._forces_b.shape[0], 3)
    if forces_b.shape != expected_shape or torques_b.shape != expected_shape:
      raise ValueError(
        f"Expected force and torque shapes {expected_shape}; got "
        f"{tuple(forces_b.shape)} and {tuple(torques_b.shape)}."
      )

    self._forces_b[:, 0, :].copy_(forces_b)
    self._torques_b[:, 0, :].copy_(torques_b)
    self._asset.permanent_wrench_composer.set_forces_and_torques(
      body_ids=self._body_ids,
      forces=self._forces_b,
      torques=self._torques_b,
    )

  # ===== reset ============================================================== #
  def reset(self, env_ids: Sequence[int] | slice | None = None) -> None:
    """清空全部或指定并行环境的 wrench buffer。

    Args:
      env_ids: 需要清空的环境索引；``None`` 表示全部环境。
    """
    selected_envs = slice(None) if env_ids is None else env_ids
    self._forces_b[selected_envs] = 0.0
    self._torques_b[selected_envs] = 0.0
