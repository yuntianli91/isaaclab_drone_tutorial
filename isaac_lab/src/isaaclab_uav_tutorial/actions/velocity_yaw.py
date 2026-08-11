"""由速度与绝对航向指令驱动 UAV 的 ActionTerm。"""

from __future__ import annotations

import math
from collections.abc import Sequence

import torch
from isaaclab.assets import Articulation
from isaaclab.envs import ManagerBasedEnv
from isaaclab.managers.action_manager import ActionTerm, ActionTermCfg
from isaaclab.utils import configclass

from isaaclab_uav_tutorial.controllers import (
  AttitudeController,
  AttitudeControllerCfg,
  VelocityYawController,
  VelocityYawControllerCfg,
)

from .body_wrench import BodyWrenchApplier


class VelocityYawAction(ActionTerm):
  """将归一化 ``[v_x, v_y, v_z, yaw]`` 转换成 body wrench。

  三轴速度均采用 world 坐标系，yaw 是 world 坐标系中的绝对航向角。
  本 ActionTerm 内部依次调用速度/航向控制器、姿态控制器和普通的
  :class:`BodyWrenchApplier`；ActionManager 只会看到这一个高层动作项。
  """

  cfg: "VelocityYawActionCfg"
  _asset: Articulation

  # ===== __init__ =========================================================== #
  def __init__(self, cfg: "VelocityYawActionCfg",
               env: ManagerBasedEnv) -> None:
    """解析 UAV 并创建两级飞行控制器。

    Args:
      cfg: 速度与绝对航向 ActionTerm 配置。
      env: 管理全部并行场景实例的环境。

    Raises:
      ValueError: 三轴速度缩放没有配置或包含非正值。
    """
    super().__init__(cfg, env)
    if cfg.velocity_scale is None:
      raise ValueError(
        "VelocityYawActionCfg.velocity_scale is required; set the three "
        "world-frame maximum speeds in m/s."
      )
    velocity_scale = torch.tensor(
      cfg.velocity_scale, dtype=torch.float32, device=self.device
    )
    if velocity_scale.shape != (3,) or torch.any(velocity_scale <= 0.0):
      raise ValueError("velocity_scale must contain three positive values.")

    self._velocity_scale = velocity_scale
    self._raw_actions = torch.zeros(self.num_envs, 4, device=self.device)
    self._processed_actions = torch.zeros_like(self._raw_actions)

    # 对该 UAV Articulation 中的全部刚体质量求和，得到整架飞机的质量。
    robot_mass = float(
      self._asset.root_physx_view.get_masses()[0].sum().item()
    )
    gravity_magnitude = float(
      torch.tensor(env.sim.cfg.gravity, device=self.device).norm().item()
    )
    self._velocity_controller = VelocityYawController(
      num_envs=self.num_envs,
      device=self.device,
      robot_mass=robot_mass,
      gravity_magnitude=gravity_magnitude,
      cfg=cfg.velocity_controller,
    )
    self._attitude_controller = AttitudeController(
      num_envs=self.num_envs,
      device=self.device,
      control_dt=env.physics_dt,
      cfg=cfg.attitude_controller,
    )
    self._wrench_applier = BodyWrenchApplier(
      asset=self._asset, body_name=cfg.body_name
    )

  # ===== action_dim ========================================================= #
  @property
  def action_dim(self) -> int:
    """返回单个环境的高层动作维数。"""
    return 4

  # ===== raw_actions ======================================================== #
  @property
  def raw_actions(self) -> torch.Tensor:
    """返回调用者传入且未经裁剪的归一化动作。"""
    return self._raw_actions

  # ===== processed_actions ================================================== #
  @property
  def processed_actions(self) -> torch.Tensor:
    """返回已转换成 SI 单位的速度和绝对航向指令。"""
    return self._processed_actions

  # ===== process_actions ==================================================== #
  def process_actions(self, actions: torch.Tensor) -> None:
    """裁剪归一化动作并转换成物理指令。

    Args:
      actions: 形状为 ``(num_envs, 4)``、期望范围为 ``[-1, 1]``
        的无量纲动作。
    """
    self._raw_actions.copy_(actions)
    normalized_actions = actions.clamp(-1.0, 1.0)
    self._processed_actions[:, 0:3] = (
      normalized_actions[:, 0:3] * self._velocity_scale
    )
    self._processed_actions[:, 3] = normalized_actions[:, 3] * math.pi

  # ===== apply_actions ====================================================== #
  def apply_actions(self) -> None:
    """运行内层飞控并向 UAV 刚体施加当前 body wrench。"""
    collective_thrust, desired_quaternion_wxyz = (
      self._velocity_controller.compute(
        desired_velocity_w=self._processed_actions[:, 0:3],
        desired_yaw=self._processed_actions[:, 3],
        current_velocity_w=self._asset.data.root_lin_vel_w,
        current_quaternion_wxyz=self._asset.data.root_quat_w,
      )
    )
    forces_b, torques_b = self._attitude_controller.compute(
      collective_thrust=collective_thrust,
      desired_quaternion_wxyz=desired_quaternion_wxyz,
      current_quaternion_wxyz=self._asset.data.root_quat_w,
      current_angular_velocity_b=self._asset.data.root_ang_vel_b,
    )
    self._wrench_applier.apply(forces_b, torques_b)

  # ===== reset ============================================================== #
  def reset(self, env_ids: Sequence[int] | slice | None = None) -> None:
    """清空指定环境的动作、姿态积分和 wrench buffer。

    Args:
      env_ids: 需要重置的环境索引；``None`` 表示全部环境。
    """
    selected_envs = slice(None) if env_ids is None else env_ids
    self._raw_actions[selected_envs] = 0.0
    self._processed_actions[selected_envs] = 0.0
    self._attitude_controller.reset(selected_envs)
    self._wrench_applier.reset(selected_envs)


@configclass
class VelocityYawActionCfg(ActionTermCfg):
  """速度与绝对航向 ActionTerm 的声明式配置。"""

  class_type: type = VelocityYawAction  # ActionTerm 实现类型。
  body_name: str = "body"               # 接收 body wrench 的唯一刚体。
  velocity_scale: tuple[                 # 三轴最大 world 速度 (m/s)。
    float, float, float
  ] | None = None
  velocity_controller: VelocityYawControllerCfg = (  # 速度/航向控制器。
    VelocityYawControllerCfg()
  )
  attitude_controller: AttitudeControllerCfg = (     # 姿态控制器。
    AttitudeControllerCfg()
  )
