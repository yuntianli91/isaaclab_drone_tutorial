"""由速度与绝对航向指令驱动 UAV 的 ActionTerm。"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import MISSING

import torch
from isaaclab.assets import Articulation
from isaaclab.envs import ManagerBasedEnv
from isaaclab.managers.action_manager import ActionTerm, ActionTermCfg
from isaaclab.utils import configclass
from isaaclab.utils.math import matrix_from_quat, quat_from_matrix

from isaaclab_uav_tutorial.controllers import (
  AttitudeController,
  AttitudeControllerCfg,
  VelocityYawController,
  VelocityYawControllerCfg,
)
from isaaclab_uav_tutorial.monitoring import PhysicsStepFlightBuffer

from .body_wrench import BodyWrenchApplier


class VelocityYawAction(ActionTerm):
  """将归一化 ``[v_x, v_y, v_z, yaw]`` 转换成 body wrench。

  三轴速度均采用 environment 坐标系，yaw 是 environment 坐标系中的绝对
  航向角。本 ActionTerm 内部依次调用速度/航向控制器、姿态控制器和
  普通的 :class:`BodyWrenchApplier`；ActionManager 只会看到这一个
  高层动作项。
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
      raise ValueError("VelocityYawActionCfg.velocity_scale is required; set "
                       "the three environment-frame maximum speeds in m/s.")
    velocity_scale = torch.tensor(cfg.velocity_scale, dtype=torch.float32,
                                  device=self.device)
    if velocity_scale.shape != (3,) or torch.any(velocity_scale <= 0.0):
      raise ValueError("velocity_scale must contain three positive values.")

    self._velocity_scale = velocity_scale
    self._raw_actions = torch.zeros(self.num_envs, 4, device=self.device)
    self._processed_actions = torch.zeros_like(self._raw_actions)
    self._rotation_ew = torch.eye(3, device=self.device).expand(
      self.num_envs, -1, -1
    ).clone()
    self._flight_buffer: PhysicsStepFlightBuffer | None = None

    # 将该 UAV Articulation 的全部刚体质量相加，得到整机质量。
    body_masses = self._asset.root_physx_view.get_masses()[0]
    robot_mass = float(body_masses.sum().item())
    gravity = torch.tensor(env.sim.cfg.gravity, device=self.device)
    gravity_magnitude = float(gravity.norm().item())
    velocity_cfg = cfg.velocity_controller
    self._velocity_controller = VelocityYawController(num_envs=self.num_envs,
                                                      device=self.device,
                                                      robot_mass=robot_mass,
                                                      gravity_magnitude=(
                                                        gravity_magnitude
                                                      ),
                                                      cfg=velocity_cfg)
    self._attitude_controller = AttitudeController(num_envs=self.num_envs,
                                                   device=self.device,
                                                   control_dt=env.physics_dt,
                                                   cfg=cfg.attitude_controller)
    self._wrench_applier = BodyWrenchApplier(asset=self._asset,
                                             body_name=cfg.body_name)

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


  # ===== configure_flight_buffer ============================================ #
  def configure_flight_buffer(self, env_id: int) -> None:
    """为指定 environment 创建 physics-rate 飞行数据 buffer。

    Args:
      env_id: 需要记录的 environment 索引。

    Raises:
      ValueError: environment 索引超出当前批量环境范围。
    """
    if env_id < 0 or env_id >= self.num_envs:
      raise ValueError("env_id must select an existing environment.")
    self._flight_buffer = PhysicsStepFlightBuffer(
      env_id=env_id, capacity=self._env.cfg.decimation,
      physics_dt=self._env.physics_dt,
      origin_we=self._env.scene.env_origins[env_id],
      rotation_ew=self._rotation_ew[env_id]
    )

  # ===== consume_flight_samples ============================================= #
  def consume_flight_samples(self) -> torch.Tensor:
    """导出当前 control interval 内全部 physics-rate 飞行数据。

    Returns:
      当前批次的 GPU tensor。

    Raises:
      RuntimeError: 尚未配置飞行数据 buffer。
    """
    if self._flight_buffer is None:
      raise RuntimeError("The physics-step flight buffer is not configured.")
    return self._flight_buffer.consume()

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
    desired_velocity_e = self._processed_actions[:, 0:3]
    desired_yaw_e = self._processed_actions[:, 3]
    current_velocity_w = self._asset.data.root_lin_vel_w
    current_velocity_e = torch.bmm(
      self._rotation_ew, current_velocity_w.unsqueeze(-1)
    ).squeeze(-1)
    current_quaternion_wb = self._asset.data.root_quat_w
    current_rotation_wb = matrix_from_quat(current_quaternion_wb)
    current_rotation_eb = torch.bmm(self._rotation_ew,
                                    current_rotation_wb)
    current_quaternion_eb = quat_from_matrix(current_rotation_eb)
    compute_velocity = self._velocity_controller.compute
    velocity_output = compute_velocity(desired_velocity_e, desired_yaw_e,
                                       current_velocity_e,
                                       current_quaternion_eb)
    collective_thrust, desired_quaternion_eb = velocity_output
    current_angular_velocity_b = self._asset.data.root_ang_vel_b
    compute_attitude = self._attitude_controller.compute
    forces_b, torques_b = compute_attitude(collective_thrust,
                                           desired_quaternion_eb,
                                           current_quaternion_eb,
                                           current_angular_velocity_b)
    if self._flight_buffer is not None:
      self._flight_buffer.record(
        position_w=self._asset.data.root_pos_w,
        quaternion_wb=current_quaternion_wb,
        linear_velocity_w=current_velocity_w,
        angular_velocity_b=current_angular_velocity_b,
        desired_velocity_e=desired_velocity_e,
        desired_yaw_e=desired_yaw_e,
        collective_thrust=collective_thrust,
        desired_quaternion_eb=desired_quaternion_eb,
        body_torque_b=torques_b
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
    if self._flight_buffer is not None:
      self._flight_buffer.clear()
    self._attitude_controller.reset(selected_envs)
    self._wrench_applier.reset(selected_envs)


@configclass
class VelocityYawActionCfg(ActionTermCfg):
  """速度与绝对航向 ActionTerm 的声明式配置。"""

  class_type: type = VelocityYawAction                        # ActionTerm。
  body_name: str = MISSING                                    # 受力刚体。
  velocity_controller: VelocityYawControllerCfg = MISSING     # 速度控制器。
  attitude_controller: AttitudeControllerCfg = MISSING        # 姿态控制器。
  velocity_scale: tuple[float, float, float] | None = None    # 速度缩放。
