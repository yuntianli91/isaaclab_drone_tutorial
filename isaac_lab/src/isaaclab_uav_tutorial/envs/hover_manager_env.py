"""Tutorial 1 使用的 ManagerBasedEnv 配置。

这个文件把 Tutorial 0 的公共场景包装成具有观测、动作和重置
接口的环境。
它只涉及以下三个 Manager：

* :class:`ObservationManager`：从仿真状态中组织批量观测；
* :class:`ActionManager`：把归一化速度/航向动作送入飞行控制器；
* :class:`EventManager`：在环境 reset 时随机化无人机初始状态。

固定悬停目标和 PID 控制器不属于环境，因此没有放在本文件中。
PID 作为外部 Agent 读取 ``observation["policy"]``，并产生与
后续 RL policy 相同语义的动作。本阶段也刻意不包含
CommandManager、RewardManager、TerminationManager 或 Gym 注册。
"""

from __future__ import annotations

from dataclasses import MISSING

import isaaclab.envs.mdp as mdp
from isaaclab.envs import ManagerBasedEnvCfg
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils import configclass

from isaaclab_uav_tutorial.actions import VelocityYawActionCfg
from isaaclab_uav_tutorial.config import Tutorial1Parameters
from isaaclab_uav_tutorial.controllers import (
  AttitudeControllerCfg,
  VelocityYawControllerCfg,
)
from isaaclab_uav_tutorial.scenes import UavObstacleSceneCfg


@configclass
class ActionsCfg:
  """声明 ActionManager 中启用的全部动作项。

  当前只有一个 ``velocity_yaw`` term，所以 ActionManager 的最终
  动作为 ``[v_x, v_y, v_z, yaw]`` 四维。
  具体参数由 :func:`create_tutorial1_manager_env_cfg` 从 YAML 填充。
  ``class_type`` 等必须使用 Python 对象表达的结构仍由 ActionCfg
  定义。
  """

  velocity_yaw = VelocityYawActionCfg()  # 速度与绝对航向动作项。


@configclass
class ObservationsCfg:
  """声明 ObservationManager 输出的纯状态观测。

  Tutorial 1 的目标由外部 PID 参数提供，因此这里不把悬停目标
  拼入观测。Tutorial 2 引入 CommandManager 后才会明确区分 state
  和 command，并决定 policy 是否能观察目标。
  """

  @configclass
  class PolicyCfg(ObsGroup):
    """供外部控制器或未来 policy 使用的 ``policy`` 观测组。

    属性声明顺序就是 ``concatenate_terms=True`` 时的 tensor
    拼接顺序：

    ``position_e(3), quaternion_eb(4),``
    ``linear_velocity_e(3), angular_velocity_b(3)``

    因此 ``observation["policy"]`` 的形状为 ``(num_envs, 13)``。
    """

    position_e = ObsTerm(func=mdp.root_pos_w,    # 官方 E 系位置项。
                         params={})              # 由 YAML 装配实体。
    quaternion_eb = ObsTerm(func=mdp.root_quat_w,  # 官方 EB 姿态项。
                            params={})             # 由 YAML 装配参数。
    linear_velocity_e = ObsTerm(func=mdp.root_lin_vel_w,  # 官方 E 系速度项。
                                params={})                 # YAML 装配实体。
    angular_velocity_b = ObsTerm(func=mdp.base_ang_vel,  # 官方角速度项。
                                 params={})              # 由 YAML 装配实体。

    # ===== __post_init__ ==================================================== #
    def __post_init__(self) -> None:
      """将四个 ObsTerm 拼接成一个 tensor。"""
      self.concatenate_terms = True  # 拼接成 (N, 13) tensor。

  policy: PolicyCfg = PolicyCfg()  # 提供给外部 Agent 的观测组。


@configclass
class EventsCfg:
  """声明 reset 阶段执行的轻量随机化事件。

  ``reset_root_state_uniform`` 先读取 Crazyflie 的默认 root state，
  再叠加采样的位姿和速度扰动。位置最终还会加上每个 clone 的
  ``env_origin``，所以 reset 不会错误地把所有无人机写回 world
  原点。

  本阶段只使用小扰动验证初始状态随机化，不展开质量、摩擦或外力等
  domain randomization。
  """

  reset_uav = EventTerm(func=mdp.reset_root_state_uniform,   # 均匀随机状态。
                        mode="reset",                        # reset 时触发。
                        params={})                           # YAML 装配参数。


@configclass
class HoverManagerEnvCfg(ManagerBasedEnvCfg):
  """组合 Tutorial 1 完整非 RL 环境的顶层配置。

  :class:`ManagerBasedEnv` 会依次创建公共 Scene、EventManager、
  ActionManager 和 ObservationManager。运行入口可以在实例化环境前
  覆盖 ``scene.num_envs``、``scene.env_spacing``、``sim.device`` 和
  ``seed``，因此这里的数量只是默认值。
  """

  scene: UavObstacleSceneCfg = MISSING               # Tutorial 0 场景。
  observations: ObservationsCfg = ObservationsCfg()  # 观测 Manager 配置。
  actions: ActionsCfg = ActionsCfg()                 # 动作 Manager 配置。
  events: EventsCfg = EventsCfg()                    # 事件 Manager 配置。

  # ===== __post_init__ ====================================================== #
  def __post_init__(self) -> None:
    """关闭本 Tutorial 不使用的 Manager 调试 UI。"""
    self.ui_window_class_type = None  # 不创建 Manager 调试 UI。


# ===== create_tutorial1_manager_env_cfg ===================================== #
def create_tutorial1_manager_env_cfg(parameters: Tutorial1Parameters
                                     ) -> HoverManagerEnvCfg:
  """用 YAML 参数构建 Tutorial 1 的 Isaac Lab 环境配置。

  Args:
    parameters: 已完成类型转换与基本验证的 YAML 参数。

  Returns:
    已填充动作资产、施力刚体和两级控制器参数的环境配置。
  """
  env_cfg = HoverManagerEnvCfg()
  runtime = parameters.runtime
  scene = parameters.scene
  env_cfg.scene = UavObstacleSceneCfg(num_envs=runtime.num_envs,
                                      env_spacing=scene.env_spacing,
                                      replicate_physics=scene.replicate_physics)
  env_cfg.sim.dt = parameters.simulation.physics_dt
  env_cfg.sim.render_interval = parameters.simulation.render_interval
  env_cfg.sim.gravity = parameters.simulation.gravity
  env_cfg.decimation = parameters.simulation.decimation
  env_cfg.seed = parameters.runtime.seed
  env_cfg.wait_for_textures = parameters.simulation.wait_for_textures
  env_cfg.viewer.eye = parameters.viewer.eye
  env_cfg.viewer.lookat = parameters.viewer.lookat

  initial_state = scene.uav_initial_state
  env_cfg.scene.uav.init_state.pos = initial_state.position
  env_cfg.scene.uav.init_state.rot = initial_state.orientation_wxyz
  env_cfg.scene.uav.init_state.lin_vel = initial_state.linear_velocity
  env_cfg.scene.uav.init_state.ang_vel = initial_state.angular_velocity

  light = scene.dome_light
  env_cfg.scene.dome_light.spawn.intensity = light.intensity
  env_cfg.scene.dome_light.spawn.color = light.color
  for obstacle_name, obstacle in scene.obstacles.items():
    obstacle_cfg = getattr(env_cfg.scene, obstacle_name)
    obstacle_cfg.init_state.pos = obstacle.position
    obstacle_cfg.spawn.size = obstacle.size
    obstacle_cfg.spawn.visual_material.diffuse_color = obstacle.color
    obstacle_cfg.spawn.visual_material.roughness = obstacle.roughness

  asset_name = parameters.action.asset_name
  asset_terms = (
    env_cfg.observations.policy.position_e,
    env_cfg.observations.policy.quaternion_eb,
    env_cfg.observations.policy.linear_velocity_e,
    env_cfg.observations.policy.angular_velocity_b,
  )
  for observation_term in asset_terms:
    observation_term.params["asset_cfg"] = SceneEntityCfg(asset_name)
  env_cfg.observations.policy.quaternion_eb.params[
    "make_quat_unique"
  ] = parameters.observations.make_quat_unique
  env_cfg.observations.policy.enable_corruption = (
    parameters.observations.enable_corruption
  )
  env_cfg.events.reset_uav.params = {
    "pose_range": parameters.reset.pose_range,
    "velocity_range": parameters.reset.velocity_range,
    "asset_cfg": SceneEntityCfg(asset_name),
  }

  action_cfg = env_cfg.actions.velocity_yaw
  action_cfg.asset_name = asset_name
  action_cfg.body_name = parameters.action.body_name
  action_cfg.velocity_scale = parameters.action.velocity_scale
  velocity = parameters.velocity_yaw
  velocity_cfg = VelocityYawControllerCfg(velocity_kp=velocity.velocity_kp,
                                          max_tilt_rad=velocity.max_tilt_rad,
                                          thrust_to_weight=(
                                            velocity.thrust_to_weight
                                          ))
  action_cfg.velocity_controller = velocity_cfg
  attitude = parameters.attitude
  attitude_cfg = AttitudeControllerCfg(attitude_kp=attitude.attitude_kp,
                                       attitude_ki=attitude.attitude_ki,
                                       attitude_kd=attitude.attitude_kd,
                                       attitude_integral_limit=(
                                         attitude.attitude_integral_limit
                                       ),
                                       moment_scale=attitude.moment_scale)
  action_cfg.attitude_controller = attitude_cfg
  return env_cfg
