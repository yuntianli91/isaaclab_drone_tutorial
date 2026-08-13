"""WXYZ 四元数与旋转矩阵的纯 Torch 转换。"""

from __future__ import annotations

import torch


# ===== matrix_from_quaternion =============================================== #
def matrix_from_quaternion(quaternion: torch.Tensor) -> torch.Tensor:
  """将 WXYZ 四元数转换成旋转矩阵。

  Args:
    quaternion: 形状为 ``(..., 4)`` 的 WXYZ 四元数。

  Returns:
    形状为 ``(..., 3, 3)`` 的旋转矩阵。
  """
  real, x_value, y_value, z_value = torch.unbind(quaternion, dim=-1)
  two_scale = 2.0 / (quaternion * quaternion).sum(dim=-1)
  matrix_values = torch.stack((
    1.0 - two_scale * (y_value**2 + z_value**2),
    two_scale * (x_value * y_value - z_value * real),
    two_scale * (x_value * z_value + y_value * real),
    two_scale * (x_value * y_value + z_value * real),
    1.0 - two_scale * (x_value**2 + z_value**2),
    two_scale * (y_value * z_value - x_value * real),
    two_scale * (x_value * z_value - y_value * real),
    two_scale * (y_value * z_value + x_value * real),
    1.0 - two_scale * (x_value**2 + y_value**2),
  ), dim=-1)
  return matrix_values.reshape(quaternion.shape[:-1] + (3, 3))


# ===== quaternion_from_matrix =============================================== #
def quaternion_from_matrix(matrix: torch.Tensor) -> torch.Tensor:
  """将旋转矩阵转换成实部非负的 WXYZ 四元数。

  Args:
    matrix: 形状为 ``(..., 3, 3)`` 的旋转矩阵。

  Returns:
    形状为 ``(..., 4)`` 的 WXYZ 四元数。

  Raises:
    ValueError: 输入末两维不是 ``(3, 3)``。
  """
  if matrix.shape[-2:] != (3, 3):
    raise ValueError("matrix must have a trailing shape of (3, 3).")

  batch_shape = matrix.shape[:-2]
  values = matrix.reshape(batch_shape + (9,))
  m00, m01, m02, m10, m11, m12, m20, m21, m22 = torch.unbind(
    values, dim=-1
  )
  squared_components = torch.stack((
    1.0 + m00 + m11 + m22,
    1.0 + m00 - m11 - m22,
    1.0 - m00 + m11 - m22,
    1.0 - m00 - m11 + m22,
  ), dim=-1).clamp_min(0.0)
  absolute_components = torch.sqrt(squared_components)
  candidates = torch.stack((
    torch.stack((squared_components[..., 0], m21 - m12, m02 - m20,
                 m10 - m01), dim=-1),
    torch.stack((m21 - m12, squared_components[..., 1], m10 + m01,
                 m02 + m20), dim=-1),
    torch.stack((m02 - m20, m10 + m01, squared_components[..., 2],
                 m12 + m21), dim=-1),
    torch.stack((m10 - m01, m20 + m02, m21 + m12,
                 squared_components[..., 3]), dim=-1),
  ), dim=-2)
  denominator = 2.0 * absolute_components.unsqueeze(-1).clamp_min(0.1)
  candidates = candidates / denominator
  best_index = absolute_components.argmax(dim=-1)
  selection = torch.nn.functional.one_hot(best_index, num_classes=4)
  quaternion = torch.sum(candidates * selection.unsqueeze(-1), dim=-2)
  return torch.where(quaternion[..., 0:1] < 0.0, -quaternion, quaternion)
