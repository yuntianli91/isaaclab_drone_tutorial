"""Tutorial 1 YAML 参数模型及其加载逻辑。"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .yaml_loader import (
  load_yaml_mapping,
  reject_unknown_keys,
  require_bool,
  require_float,
  require_float_tuple,
  require_int,
  require_mapping,
  require_range_mapping,
  require_string,
)


@dataclass(frozen=True)
class AppLauncherParameters:
  """Isaac Lab AppLauncher 参数。"""

  headless: bool
  livestream: int
  enable_cameras: bool
  xr: bool
  device: str
  experience: str
  rendering_mode: str

  # ===== to_dict ============================================================ #
  def to_dict(self) -> dict[str, object]:
    """转换成 :class:`AppLauncher` 接受的参数字典。"""
    return {
      "headless": self.headless,
      "livestream": self.livestream,
      "enable_cameras": self.enable_cameras,
      "xr": self.xr,
      "device": self.device,
      "device_explicit": True,
      "experience": self.experience,
      "rendering_mode": self.rendering_mode,
    }


@dataclass(frozen=True)
class RuntimeParameters:
  """入口运行参数。"""

  num_envs: int
  max_steps: int
  seed: int


@dataclass(frozen=True)
class TaskParameters:
  """固定悬停任务参数。"""

  hover_height: float
  target_yaw: float


@dataclass(frozen=True)
class SimulationParameters:
  """仿真频率、重力和加载参数。"""

  physics_dt: float
  decimation: int
  render_interval: int
  gravity: tuple[float, float, float]
  wait_for_textures: bool


@dataclass(frozen=True)
class ViewerParameters:
  """默认相机参数。"""

  eye: tuple[float, float, float]
  lookat: tuple[float, float, float]


@dataclass(frozen=True)
class UavInitialStateParameters:
  """UAV 根刚体初始状态。"""

  position: tuple[float, float, float]
  orientation_wxyz: tuple[float, float, float, float]
  linear_velocity: tuple[float, float, float]
  angular_velocity: tuple[float, float, float]


@dataclass(frozen=True)
class DomeLightParameters:
  """场景穹顶灯参数。"""

  intensity: float
  color: tuple[float, float, float]


@dataclass(frozen=True)
class ObstacleParameters:
  """单个静态柱体参数。"""

  position: tuple[float, float, float]
  size: tuple[float, float, float]
  color: tuple[float, float, float]
  roughness: float


@dataclass(frozen=True)
class SceneParameters:
  """公共场景的可序列化参数。"""

  env_spacing: float
  replicate_physics: bool
  uav_initial_state: UavInitialStateParameters
  dome_light: DomeLightParameters
  obstacles: dict[str, ObstacleParameters]


@dataclass(frozen=True)
class ObservationParameters:
  """ObservationManager 的数值和布尔参数。"""

  make_quat_unique: bool
  enable_corruption: bool


@dataclass(frozen=True)
class ResetParameters:
  """reset 时叠加到 UAV 默认状态的采样范围。"""

  pose_range: dict[str, tuple[float, float]]
  velocity_range: dict[str, tuple[float, float]]


@dataclass(frozen=True)
class ActionParameters:
  """高层速度与航向动作参数。"""

  asset_name: str
  body_name: str
  velocity_scale: tuple[float, float, float] | None


@dataclass(frozen=True)
class PositionCommandPIDParameters:
  """外层 Planner baseline 参数。"""

  position_kp: tuple[float, float, float]
  position_ki: tuple[float, float, float]
  position_integral_limit: float


@dataclass(frozen=True)
class VelocityYawControllerParameters:
  """速度与绝对航向控制器参数。"""

  velocity_kp: tuple[float, float, float]
  max_tilt_rad: float
  thrust_to_weight: float


@dataclass(frozen=True)
class AttitudeControllerParameters:
  """姿态控制器参数。"""

  attitude_kp: tuple[float, float, float]
  attitude_ki: tuple[float, float, float]
  attitude_kd: tuple[float, float, float]
  attitude_integral_limit: float
  moment_scale: float


@dataclass(frozen=True)
class FlightLoggingParameters:
  """单环境飞行日志参数。"""

  enabled: bool
  env_id: int
  output_root: str
  flush_interval: int
  plot: bool


@dataclass(frozen=True)
class Tutorial1Parameters:
  """Tutorial 1 YAML 中全部受支持参数的只读集合。"""

  app: AppLauncherParameters
  runtime: RuntimeParameters
  task: TaskParameters
  simulation: SimulationParameters
  viewer: ViewerParameters
  scene: SceneParameters
  observations: ObservationParameters
  reset: ResetParameters
  action: ActionParameters
  position_command_pid: PositionCommandPIDParameters
  velocity_yaw: VelocityYawControllerParameters
  attitude: AttitudeControllerParameters
  flight_logging: FlightLoggingParameters


# ===== _positive ============================================================ #
def _positive(value: float, location: str) -> float:
  """验证浮点参数严格为正。"""
  if value <= 0.0:
    raise ValueError(f"{location} must be positive.")
  return value


# ===== _load_obstacle ======================================================= #
def _load_obstacle(data: object, location: str) -> ObstacleParameters:
  """加载单个柱体参数。"""
  if not isinstance(data, Mapping):
    raise ValueError(f"{location} must be a mapping.")
  obstacle_data: Mapping[str, Any] = data
  obstacle_keys = ("position", "size", "color", "roughness")
  reject_unknown_keys(obstacle_data, obstacle_keys, location)
  position = require_float_tuple(obstacle_data, "position", location, 3)
  size = require_float_tuple(obstacle_data, "size", location, 3)
  color = require_float_tuple(obstacle_data, "color", location, 3)
  roughness = require_float(obstacle_data, "roughness", location)
  return ObstacleParameters(position=position, size=size, color=color,
                            roughness=roughness)


# ===== load_tutorial1_parameters ============================================ #
def load_tutorial1_parameters(config_path: str | Path) -> Tutorial1Parameters:
  """读取并验证 Tutorial 1 YAML 参数。"""
  root = load_yaml_mapping(config_path)
  app = require_mapping(root, "app", "root")
  runtime = require_mapping(root, "runtime", "root")
  task = require_mapping(root, "task", "root")
  simulation = require_mapping(root, "simulation", "root")
  viewer = require_mapping(root, "viewer", "root")
  scene = require_mapping(root, "scene", "root")
  initial_state = require_mapping(scene, "uav_initial_state", "root.scene")
  dome_light = require_mapping(scene, "dome_light", "root.scene")
  obstacles = require_mapping(scene, "obstacles", "root.scene")
  observations = require_mapping(root, "observations", "root")
  reset = require_mapping(root, "reset", "root")
  action = require_mapping(root, "action", "root")
  controllers = require_mapping(root, "controllers", "root")
  flight_logging = require_mapping(root, "flight_logging", "root")
  position = require_mapping(controllers, "position_command_pid",
                             "root.controllers")
  velocity = require_mapping(controllers, "velocity_yaw", "root.controllers")
  attitude = require_mapping(controllers, "attitude", "root.controllers")

  root_keys = (
    "app", "runtime", "task", "simulation", "viewer", "scene",
    "observations", "reset", "action", "controllers", "flight_logging",
  )
  reject_unknown_keys(root, root_keys, "root")
  app_keys = ("headless", "livestream", "enable_cameras", "xr", "device",
              "experience", "rendering_mode")
  reject_unknown_keys(app, app_keys, "root.app")
  reject_unknown_keys(runtime, ("num_envs", "max_steps", "seed"),
                      "root.runtime")
  reject_unknown_keys(task, ("hover_height", "target_yaw"), "root.task")
  simulation_keys = ("physics_dt", "decimation", "render_interval", "gravity",
                     "wait_for_textures")
  reject_unknown_keys(simulation, simulation_keys, "root.simulation")
  reject_unknown_keys(viewer, ("eye", "lookat"), "root.viewer")
  scene_keys = ("env_spacing", "replicate_physics", "uav_initial_state",
                "dome_light", "obstacles")
  reject_unknown_keys(scene, scene_keys, "root.scene")
  initial_state_keys = (
    "position", "orientation_wxyz", "linear_velocity", "angular_velocity",
  )
  reject_unknown_keys(initial_state, initial_state_keys,
                      "root.scene.uav_initial_state")
  reject_unknown_keys(dome_light, ("intensity", "color"),
                      "root.scene.dome_light")
  obstacle_names = ("pillar_tall", "pillar_medium", "pillar_low")
  reject_unknown_keys(obstacles, obstacle_names, "root.scene.obstacles")
  reject_unknown_keys(observations,
                      ("make_quat_unique", "enable_corruption"),
                      "root.observations")
  reject_unknown_keys(reset, ("pose_range", "velocity_range"), "root.reset")
  reject_unknown_keys(action, ("asset_name", "body_name", "velocity_scale"),
                      "root.action")
  controller_keys = ("position_command_pid", "velocity_yaw", "attitude")
  reject_unknown_keys(controllers, controller_keys, "root.controllers")
  position_keys = ("position_kp", "position_ki", "position_integral_limit")
  reject_unknown_keys(position, position_keys,
                      "root.controllers.position_command_pid")
  velocity_keys = ("velocity_kp", "max_tilt_rad", "thrust_to_weight")
  reject_unknown_keys(velocity, velocity_keys,
                      "root.controllers.velocity_yaw")
  attitude_keys = (
    "attitude_kp", "attitude_ki", "attitude_kd",
    "attitude_integral_limit", "moment_scale",
  )
  reject_unknown_keys(attitude, attitude_keys, "root.controllers.attitude")
  logging_keys = ("enabled", "env_id", "output_root", "flush_interval",
                  "plot")
  reject_unknown_keys(flight_logging, logging_keys, "root.flight_logging")

  num_envs = require_int(runtime, "num_envs", "root.runtime")
  max_steps = require_int(runtime, "max_steps", "root.runtime")
  decimation = require_int(simulation, "decimation", "root.simulation")
  render_interval = require_int(simulation, "render_interval",
                                "root.simulation")
  if num_envs < 1:
    raise ValueError("root.runtime.num_envs must be at least one.")
  if max_steps < 0:
    raise ValueError("root.runtime.max_steps must be non-negative.")
  if decimation < 1 or render_interval < 1:
    raise ValueError("root.simulation decimation and render_interval must be "
                     "positive.")

  logging_env_id = require_int(flight_logging, "env_id",
                               "root.flight_logging")
  flush_interval = require_int(flight_logging, "flush_interval",
                               "root.flight_logging")
  if logging_env_id < 0 or logging_env_id >= num_envs:
    raise ValueError("root.flight_logging.env_id must select an existing "
                     "environment.")
  if flush_interval < 1:
    raise ValueError("root.flight_logging.flush_interval must be positive.")

  livestream = require_int(app, "livestream", "root.app")
  if livestream not in {0, 1, 2}:
    raise ValueError("root.app.livestream must be one of 0, 1, or 2.")
  rendering_mode = require_string(app, "rendering_mode", "root.app")
  if rendering_mode not in {"balanced", "performance", "quality"}:
    raise ValueError("root.app.rendering_mode must be balanced, performance, "
                     "or quality.")
  experience = app.get("experience")
  if not isinstance(experience, str):
    raise ValueError("root.app.experience must be a string.")

  orientation = require_float_tuple(initial_state, "orientation_wxyz",
                                    "root.scene.uav_initial_state", 4)
  if math.isclose(sum(value * value for value in orientation), 0.0):
    raise ValueError("root.scene.uav_initial_state.orientation_wxyz cannot be "
                     "zero.")

  velocity_scale = None
  if action.get("velocity_scale") is not None:
    velocity_scale = require_float_tuple(action, "velocity_scale",
                                         "root.action", 3)
    if any(value <= 0.0 for value in velocity_scale):
      raise ValueError("root.action.velocity_scale values must be positive.")

  range_keys = ("x", "y", "z", "roll", "pitch", "yaw")
  obstacle_parameters = {
    name: _load_obstacle(obstacles.get(name),
                         f"root.scene.obstacles.{name}")
    for name in obstacle_names
  }

  headless = require_bool(app, "headless", "root.app")
  enable_cameras = require_bool(app, "enable_cameras", "root.app")
  xr = require_bool(app, "xr", "root.app")
  device = require_string(app, "device", "root.app")
  app_parameters = AppLauncherParameters(headless=headless,
                                         livestream=livestream,
                                         enable_cameras=enable_cameras, xr=xr,
                                         device=device, experience=experience,
                                         rendering_mode=rendering_mode)

  seed = require_int(runtime, "seed", "root.runtime")
  runtime_parameters = RuntimeParameters(num_envs=num_envs,
                                         max_steps=max_steps, seed=seed)

  hover_height = _positive(require_float(task, "hover_height", "root.task"),
                           "root.task.hover_height")
  target_yaw = require_float(task, "target_yaw", "root.task")
  task_parameters = TaskParameters(hover_height=hover_height,
                                   target_yaw=target_yaw)

  physics_value = require_float(simulation, "physics_dt", "root.simulation")
  physics_dt = _positive(physics_value, "root.simulation.physics_dt")
  gravity = require_float_tuple(simulation, "gravity", "root.simulation", 3)
  wait_for_textures = require_bool(simulation, "wait_for_textures",
                                   "root.simulation")
  simulation_parameters = SimulationParameters(physics_dt=physics_dt,
                                               decimation=decimation,
                                               render_interval=render_interval,
                                               gravity=gravity,
                                               wait_for_textures=(
                                                 wait_for_textures
                                               ))

  eye = require_float_tuple(viewer, "eye", "root.viewer", 3)
  lookat = require_float_tuple(viewer, "lookat", "root.viewer", 3)
  viewer_parameters = ViewerParameters(eye=eye, lookat=lookat)

  initial_location = "root.scene.uav_initial_state"
  initial_position = require_float_tuple(initial_state, "position",
                                         initial_location, 3)
  linear_velocity = require_float_tuple(initial_state, "linear_velocity",
                                        initial_location, 3)
  angular_velocity = require_float_tuple(initial_state, "angular_velocity",
                                         initial_location, 3)
  uav_state = UavInitialStateParameters(position=initial_position,
                                        orientation_wxyz=orientation,
                                        linear_velocity=linear_velocity,
                                        angular_velocity=angular_velocity)
  light_intensity = require_float(dome_light, "intensity",
                                  "root.scene.dome_light")
  light_color = require_float_tuple(dome_light, "color",
                                    "root.scene.dome_light", 3)
  light_parameters = DomeLightParameters(intensity=light_intensity,
                                         color=light_color)
  env_spacing_value = require_float(scene, "env_spacing", "root.scene")
  env_spacing = _positive(env_spacing_value, "root.scene.env_spacing")
  replicate_physics = require_bool(scene, "replicate_physics", "root.scene")
  scene_parameters = SceneParameters(env_spacing=env_spacing,
                                     replicate_physics=replicate_physics,
                                     uav_initial_state=uav_state,
                                     dome_light=light_parameters,
                                     obstacles=obstacle_parameters)

  make_quat_unique = require_bool(observations, "make_quat_unique",
                                  "root.observations")
  enable_corruption = require_bool(observations, "enable_corruption",
                                   "root.observations")
  observation_parameters = ObservationParameters(make_quat_unique,
                                                 enable_corruption)

  pose_range = require_range_mapping(reset, "pose_range", "root.reset",
                                     range_keys)
  velocity_range = require_range_mapping(reset, "velocity_range", "root.reset",
                                         range_keys)
  reset_parameters = ResetParameters(pose_range=pose_range,
                                     velocity_range=velocity_range)

  asset_name = require_string(action, "asset_name", "root.action")
  body_name = require_string(action, "body_name", "root.action")
  action_parameters = ActionParameters(asset_name=asset_name,
                                       body_name=body_name,
                                       velocity_scale=velocity_scale)

  position_location = "root.controllers.position_command_pid"
  position_kp = require_float_tuple(position, "position_kp",
                                    position_location, 3)
  position_ki = require_float_tuple(position, "position_ki",
                                    position_location, 3)
  position_limit = require_float(position, "position_integral_limit",
                                 position_location)
  position_parameters = PositionCommandPIDParameters(position_kp, position_ki,
                                                     position_limit)

  velocity_location = "root.controllers.velocity_yaw"
  velocity_kp = require_float_tuple(velocity, "velocity_kp",
                                    velocity_location, 3)
  max_tilt_rad = require_float(velocity, "max_tilt_rad", velocity_location)
  thrust_to_weight = require_float(velocity, "thrust_to_weight",
                                   velocity_location)
  velocity_parameters = VelocityYawControllerParameters(velocity_kp,
                                                        max_tilt_rad,
                                                        thrust_to_weight)

  attitude_location = "root.controllers.attitude"
  attitude_kp = require_float_tuple(attitude, "attitude_kp",
                                    attitude_location, 3)
  attitude_ki = require_float_tuple(attitude, "attitude_ki",
                                    attitude_location, 3)
  attitude_kd = require_float_tuple(attitude, "attitude_kd",
                                    attitude_location, 3)
  attitude_limit = require_float(attitude, "attitude_integral_limit",
                                 attitude_location)
  moment_scale = require_float(attitude, "moment_scale", attitude_location)
  attitude_parameters = AttitudeControllerParameters(attitude_kp, attitude_ki,
                                                     attitude_kd,
                                                     attitude_limit,
                                                     moment_scale)

  logging_enabled = require_bool(flight_logging, "enabled",
                                 "root.flight_logging")
  output_root = require_string(flight_logging, "output_root",
                               "root.flight_logging")
  if not output_root.strip():
    raise ValueError("root.flight_logging.output_root cannot be empty.")
  plot = require_bool(flight_logging, "plot", "root.flight_logging")
  logging_parameters = FlightLoggingParameters(
    enabled=logging_enabled, env_id=logging_env_id,
    output_root=output_root, flush_interval=flush_interval, plot=plot
  )

  return Tutorial1Parameters(app=app_parameters, runtime=runtime_parameters,
                             task=task_parameters,
                             simulation=simulation_parameters,
                             viewer=viewer_parameters,
                             scene=scene_parameters,
                             observations=observation_parameters,
                             reset=reset_parameters,
                             action=action_parameters,
                             position_command_pid=position_parameters,
                             velocity_yaw=velocity_parameters,
                             attitude=attitude_parameters,
                             flight_logging=logging_parameters)
