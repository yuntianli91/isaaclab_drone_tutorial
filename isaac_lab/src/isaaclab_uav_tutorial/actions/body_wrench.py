"""基于机体合推力和合力矩的 UAV ActionTerm。"""

from __future__ import annotations

from collections.abc import Sequence

import torch
from isaaclab.assets import Articulation
from isaaclab.envs import ManagerBasedEnv
from isaaclab.managers.action_manager import ActionTerm, ActionTermCfg
from isaaclab.utils import configclass


class UavBodyWrenchAction(ActionTerm):
  """将四维归一化动作映射为作用在无人机机体上的推力和力矩。

  输入动作的形状为 ``(num_envs, 4)``，每一维都限制在 ``[-1, 1]``：

  .. code-block:: text

    action = [collective_thrust, roll_moment, pitch_moment, yaw_moment]

  总推力（第 0 维）沿机体系 Z 轴方向施加；roll、pitch、yaw
  力矩（第 1、2、3 维）分别绕机体系 X、Y、Z 轴施加。

  这个动作项采用整机 body-wrench 控制抽象，不模拟独立电机、螺旋桨动力学或
  每个旋翼的单独推力。默认缩放值与本机 Isaac Lab 2.3.2 Direct Crazyflie
  任务保持一致。

  ``ActionTerm`` 有两个不同调用频率的方法：

  * :meth:`process_actions` 每个 environment step 调用一次，完成裁剪和
    物理量缩放；
  * :meth:`apply_actions` 每个 physics step 调用一次，在 decimation
    期间重复施加上一次动作。
  """

  cfg: "UavBodyWrenchActionCfg"
  _asset: Articulation

  # ===== __init__ =========================================================== #
  def __init__(self, cfg: "UavBodyWrenchActionCfg",
               env: ManagerBasedEnv) -> None:
    """解析 UAV 并创建批量动作和 wrench buffer。

    Args:
      cfg: UAV wrench 动作配置。
      env: 管理全部并行场景实例的环境。
    """
    # 父类会根据 cfg.asset_name 从 env.scene 中取得资产，并保存到 self._asset。
    super().__init__(cfg, env)

    # raw_actions 保存调用者传入的原始动作；processed_actions 保存裁剪后的动作。
    # 两者均始终保留 batch 维度，避免并行环境控制过程中发生 CPU/GPU 数据拆分。
    self._raw_actions = torch.zeros(self.num_envs, 4, device=self.device)
    self._processed_actions = torch.zeros_like(self._raw_actions)

    # WrenchComposer 期望形状为 (num_envs, selected_bodies, 3)。
    # 这里只有一个机体 link，
    # 因此中间维度为 1。force 和 torque 分别使用两个独立 buffer。
    self._forces = torch.zeros(self.num_envs, 1, 3, device=self.device)
    self._torques = torch.zeros_like(self._forces)

    # body_name 指定承受整机合推力与合力矩的唯一刚体 link。
    # find_bodies 返回
    # (body_ids, body_names)，这里只需要传给 WrenchComposer 的 body_ids。
    self._body_ids = self._asset.find_bodies(cfg.body_name)[0]

    # 对当前 UAV Articulation 包含的所有刚体质量求和，
    # 得到整机总质量；再乘重力加速度幅值，得到整机重力 (N)。
    # collective_thrust 按整机重力的倍数缩放，避免写死整机质量。
    robot_mass = self._asset.root_physx_view.get_masses()[0].sum()
    gravity_magnitude = torch.tensor(
      env.sim.cfg.gravity, device=self.device
    ).norm()
    self._robot_weight = float((robot_mass * gravity_magnitude).item())

  # ===== action_dim ========================================================= #
  @property
  def action_dim(self) -> int:
    """返回单个环境的动作维度。

    Returns:
      不包含并行环境 batch 维度的动作维数。
    """
    return 4

  # ===== raw_actions ======================================================== #
  @property
  def raw_actions(self) -> torch.Tensor:
    """返回未经裁剪的动作。

    Returns:
      形状为 ``(num_envs, 4)`` 的原始动作。
    """
    return self._raw_actions

  # ===== processed_actions ================================================== #
  @property
  def processed_actions(self) -> torch.Tensor:
    """返回裁剪后的动作。

    Returns:
      形状为 ``(num_envs, 4)``、范围为 ``[-1, 1]`` 的动作。
    """
    return self._processed_actions

  # ===== process_actions ==================================================== #
  def process_actions(self, actions: torch.Tensor) -> None:
    """缓存动作，并将无量纲动作转换为推力与力矩。

    Args:
      actions: Policy/Controller 输出的归一化动作。
    """
    # 保留原始输入便于调试或日志记录；实际施加到仿真的动作必须先裁剪。
    self._raw_actions.copy_(actions)
    self._processed_actions.copy_(actions.clamp(-1.0, 1.0))

    # 将总推力（第 0 维）从 [-1, 1] 线性映射到
    # [0, thrust_to_weight * robot_weight]。
    # Crazyflie 正立且无其他加速度需求时，悬停推力约等于 robot_weight，对应的
    # 归一化动作约为 2 / 1.9 - 1 = 0.0526，而不是 0。
    self._forces[:, 0, 2] = (
      self.cfg.thrust_to_weight
      * self._robot_weight
      * (self._processed_actions[:, 0] + 1.0)
      / 2.0
    )

    # roll、pitch、yaw 力矩（第 1、2、3 维）直接缩放为机体系力矩；
    # forces 的 X/Y 分量保持为 0。
    self._torques[:, 0, :] = (
      self.cfg.moment_scale * self._processed_actions[:, 1:4]
    )

  # ===== apply_actions ====================================================== #
  def apply_actions(self) -> None:
    """通过永久 WrenchComposer 将当前 buffer 施加到指定机体 link。"""
    # ActionManager 会在每个 physics step 调用 permanent composer。
    # 每次调用都更新同一个持久 wrench，而不是不断向上一帧的 wrench 做累加。
    self._asset.permanent_wrench_composer.set_forces_and_torques(
      body_ids=self._body_ids, forces=self._forces, torques=self._torques
    )

  # ===== reset ============================================================== #
  def reset(self, env_ids: Sequence[int] | None = None) -> None:
    """清空指定环境的动作和 wrench buffer。

    Args:
      env_ids: 需要重置的环境索引；``None`` 表示全部环境。
    """
    if env_ids is None:
      # slice(None) 可以直接索引所有环境，同时避免额外创建索引 tensor。
      env_ids = slice(None)
    self._raw_actions[env_ids] = 0.0
    self._processed_actions[env_ids] = 0.0
    self._forces[env_ids] = 0.0
    self._torques[env_ids] = 0.0


@configclass
class UavBodyWrenchActionCfg(ActionTermCfg):
  """UAV body-wrench ActionTerm 的声明式配置。

  ``class_type`` 告诉 ActionManager 要实例化的 ActionTerm；
  ``asset_name`` 由使用该配置的环境动作组提供。默认缩放值与本机
  Isaac Lab 2.3.2 Direct Crazyflie 示例保持一致。
  """

  class_type: type = UavBodyWrenchAction  # ActionTerm 实现类型。
  body_name: str = "body"                 # 承受合力与力矩的 link。
  thrust_to_weight: float = 1.9           # 最大推重比。
  moment_scale: float = 0.01              # 力矩缩放 (N·m)。
