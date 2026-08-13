"""Tutorial 1：使用 ManagerBasedEnv 封装场景并通过 PID 控制 UAV。

本文件是独立可执行入口。环境只定义观测、动作和重置语义，
导入的控制器仍是外部 Agent。
"""

# AppLauncher 必须先启动 Isaac Sim，之后才能导入仿真模块。
# ruff: noqa: E402

from __future__ import annotations

import argparse
from pathlib import Path

import yaml
from isaaclab.app import AppLauncher

from isaaclab_uav_tutorial.config import load_tutorial1_parameters

DEFAULT_CONFIG_PATH = (
  Path(__file__).resolve().parents[1]
  / "configs"
  / "tutorials"
  / "tutorial1.yaml"
)

parser_description = "Run the ManagerBasedEnv UAV hover PID baseline."
parser = argparse.ArgumentParser(description=parser_description)
parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH,
                    help="Path to the Tutorial 1 YAML configuration file.")
args_cli = parser.parse_args()

try:
  tutorial_parameters = load_tutorial1_parameters(args_cli.config)
except (OSError, ValueError, yaml.YAMLError) as error:
  parser.error(f"failed to load --config: {error}")

num_envs = tutorial_parameters.runtime.num_envs
hover_height = tutorial_parameters.task.hover_height
max_steps = tutorial_parameters.runtime.max_steps
seed = tutorial_parameters.runtime.seed
velocity_scale = tutorial_parameters.action.velocity_scale
if velocity_scale is None:
  parser.error("action.velocity_scale is null; set it in the selected YAML "
               "file")
app_launcher = AppLauncher(tutorial_parameters.app.to_dict())
simulation_app = app_launcher.app


import torch
from isaaclab.envs import ManagerBasedEnv

from isaaclab_uav_tutorial.actions import VelocityYawAction
from isaaclab_uav_tutorial.controllers import (
  PositionCommandPID,
  PositionCommandPIDCfg,
)
from isaaclab_uav_tutorial.envs import create_tutorial1_manager_env_cfg
from isaaclab_uav_tutorial.monitoring import FlightLogger


# ===== main ================================================================= #
def main() -> None:
  """创建环境并运行外部批量 PID 控制器。"""
  env_cfg = create_tutorial1_manager_env_cfg(tutorial_parameters)
  env_cfg.scene.num_envs = num_envs
  env_cfg.sim.device = tutorial_parameters.app.device
  env_cfg.seed = seed
  env_cfg.actions.velocity_yaw.velocity_scale = velocity_scale
  env = ManagerBasedEnv(cfg=env_cfg)
  flight_logger: FlightLogger | None = None

  try:
    observation, _ = env.reset(seed=seed)
    policy_observation = observation["policy"]

    logging_parameters = tutorial_parameters.flight_logging
    if logging_parameters.enabled:
      output_root = Path(logging_parameters.output_root).expanduser()
      if not output_root.is_absolute():
        output_root = Path(__file__).resolve().parents[1] / output_root
      flight_logger = FlightLogger(
        output_root=output_root, env_id=logging_parameters.env_id,
        flush_interval=logging_parameters.flush_interval,
        plot=logging_parameters.plot
      )
      print(f"[INFO] Flight log directory: {flight_logger.run_directory}")

    action_term = env.action_manager.get_term("velocity_yaw")
    if not isinstance(action_term, VelocityYawAction):
      raise TypeError("The velocity_yaw action term has an unexpected type.")
    if logging_parameters.enabled:
      action_term.configure_flight_buffer(logging_parameters.env_id)

    pid_parameters = tutorial_parameters.position_command_pid
    position_kp = pid_parameters.position_kp
    position_ki = pid_parameters.position_ki
    position_limit = pid_parameters.position_integral_limit
    controller_cfg = PositionCommandPIDCfg(position_kp, position_ki,
                                           position_limit)
    controller = PositionCommandPID(num_envs=env.num_envs,
                                    device=env.device,
                                    control_dt=env.step_dt,
                                    velocity_scale=velocity_scale,
                                    cfg=controller_cfg)
    target_position = torch.zeros(env.num_envs, 3, device=env.device)
    target_position[:, 2] = hover_height
    target_yaw = torch.full((env.num_envs,),
                            tutorial_parameters.task.target_yaw,
                            device=env.device)

    print(f"[INFO] Environment ready: num_envs={env.num_envs}, "
          f"device={env.device}, "
          f"physics_dt={env.physics_dt:.3f} s, control_dt={env.step_dt:.3f} s.")
    print(f"[INFO] policy observation shape={tuple(policy_observation.shape)}, "
          f"action shape=({env.num_envs}, "
          f"{env.action_manager.total_action_dim}).")
    print("[INFO] Observation order: position_e(3), quaternion_eb(4), "
          "linear_velocity_e(3), angular_velocity_b(3).")
    print("[INFO] Action order: normalized environment velocity(3), "
          "normalized absolute yaw(1).")

    step_count = 0
    tracked_error_sum = 0.0
    tracked_samples = 0
    tracking_start = (
      int(0.75 * max_steps) if max_steps > 0 else 0
    )
    last_action = torch.zeros(env.num_envs, 4, device=env.device)

    while simulation_app.is_running() and (
      max_steps == 0 or step_count < max_steps
    ):
      last_action = controller.compute(policy_observation, target_position,
                                       target_yaw)
      observation, _ = env.step(last_action)
      if flight_logger is not None:
        flight_samples = action_term.consume_flight_samples()
        flight_logger.log_batch(flight_samples)
      policy_observation = observation["policy"]
      step_count += 1

      if step_count >= tracking_start:
        position_delta = policy_observation[:, 0:3] - target_position
        position_error = torch.linalg.vector_norm(position_delta, dim=-1)
        tracked_error_sum += float(position_error.sum().item())
        tracked_samples += env.num_envs

    finite_tensors = (
      torch.isfinite(policy_observation).all()
      and torch.isfinite(last_action).all()
    )
    print(f"[INFO] Finished after {step_count} environment steps; "
          f"tensors_finite={bool(finite_tensors)}.")
    if tracked_samples > 0:
      mean_error = tracked_error_sum / tracked_samples
      final_delta = policy_observation[:, 0:3] - target_position
      final_error = torch.linalg.vector_norm(final_delta, dim=-1)
      print(f"[RESULT] mean_position_error_last_quarter={mean_error:.4f} m, "
            f"final_mean={final_error.mean().item():.4f} m, "
            f"final_max={final_error.max().item():.4f} m.")
  finally:
    try:
      if flight_logger is not None:
        flight_logger.close()
        print(f"[INFO] Flight CSV written to: {flight_logger.csv_path}")
    finally:
      env.close()


if __name__ == "__main__":
  try:
    main()
  finally:
    skip_cleanup = tutorial_parameters.app.headless or max_steps > 0
    simulation_app.close(skip_cleanup=skip_cleanup)
