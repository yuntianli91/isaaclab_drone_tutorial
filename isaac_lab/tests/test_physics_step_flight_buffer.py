"""PhysicsStepFlightBuffer 的坐标变换测试。"""

from __future__ import annotations

import math

import torch

from isaaclab_uav_tutorial.monitoring import PhysicsStepFlightBuffer


# ===== test_complete_world_to_environment_transform ========================= #
def test_complete_world_to_environment_transform() -> None:
  """验证位置、自由向量和姿态均执行完整的 ``W → E`` 变换。"""
  rotation_ew = torch.tensor(((0.0, 1.0, 0.0),
                              (-1.0, 0.0, 0.0),
                              (0.0, 0.0, 1.0)))
  buffer = PhysicsStepFlightBuffer(
    env_id=0, capacity=1, physics_dt=0.01,
    origin_we=torch.tensor((1.0, 2.0, 0.0)),
    rotation_ew=rotation_ew
  )
  quaternion_identity = torch.tensor(((1.0, 0.0, 0.0, 0.0),))
  buffer.record(
    position_w=torch.tensor(((2.0, 2.0, 0.0),)),
    quaternion_wb=quaternion_identity,
    linear_velocity_w=torch.tensor(((1.0, 0.0, 0.0),)),
    angular_velocity_b=torch.zeros(1, 3),
    desired_velocity_e=torch.zeros(1, 3),
    desired_yaw_e=torch.zeros(1),
    collective_thrust=torch.zeros(1),
    desired_quaternion_eb=quaternion_identity,
    body_torque_b=torch.zeros(1, 3)
  )

  sample = buffer.consume()[0]
  assert torch.allclose(sample[1:4], torch.tensor((0.0, -1.0, 0.0)))
  assert torch.allclose(sample[8:11], torch.tensor((0.0, -1.0, 0.0)))
  expected_quaternion_eb = torch.tensor((math.sqrt(0.5), 0.0, 0.0,
                                         -math.sqrt(0.5)))
  assert torch.allclose(sample[4:8], expected_quaternion_eb, atol=1.0e-6)
