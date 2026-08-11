"""Tutorial 1：使用 ManagerBasedEnv 封装场景并通过 PID 控制 UAV。

本文件是独立可执行入口。环境只定义观测、动作和重置语义，导入的控制器
仍是外部 Agent。
"""

# AppLauncher 必须先启动 Isaac Sim，之后才能导入仿真模块。
# ruff: noqa: E402

from __future__ import annotations

import argparse

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(
  description="Run the ManagerBasedEnv UAV hover PID baseline."
)
parser.add_argument(
  "--num_envs", type=int, default=4, help="Number of parallel environments."
)
parser.add_argument(
  "--env_spacing", type=float, default=6.0,
  help="Spacing between environment origins in metres.",
)
parser.add_argument(
  "--hover_height", type=float, default=1.0,
  help="Fixed hover height relative to each environment origin.",
)
parser.add_argument(
  "--velocity_scale", type=float, nargs=3, required=True,
  metavar=("VX_MAX", "VY_MAX", "VZ_MAX"),
  help="Required world-frame maximum speeds in m/s; no default is assumed.",
)
parser.add_argument(
  "--max_steps", type=int, default=500,
  help=(
    "Number of environment steps before exit; use 0 to run until the app "
    "closes."
  ),
)
parser.add_argument(
  "--seed", type=int, default=42, help="Seed used by the reset EventManager."
)
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

if args_cli.num_envs < 1:
  parser.error("--num_envs must be at least 1")
if args_cli.env_spacing <= 0.0:
  parser.error("--env_spacing must be positive")
if args_cli.hover_height <= 0.0:
  parser.error("--hover_height must be positive")
if any(value <= 0.0 for value in args_cli.velocity_scale):
  parser.error("all --velocity_scale values must be positive")
if args_cli.max_steps < 0:
  parser.error("--max_steps must be non-negative")
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app


import torch
from isaaclab.envs import ManagerBasedEnv

from isaaclab_uav_tutorial.controllers import PositionCommandPID
from isaaclab_uav_tutorial.envs import HoverManagerEnvCfg


# ===== main ================================================================= #
def main() -> None:
  """创建环境并运行外部批量 PID 控制器。"""
  env_cfg = HoverManagerEnvCfg()
  env_cfg.scene.num_envs = args_cli.num_envs
  env_cfg.scene.env_spacing = args_cli.env_spacing
  env_cfg.sim.device = args_cli.device
  env_cfg.seed = args_cli.seed
  env_cfg.actions.velocity_yaw.velocity_scale = tuple(
    args_cli.velocity_scale
  )
  env = ManagerBasedEnv(cfg=env_cfg)

  try:
    observation, _ = env.reset(seed=args_cli.seed)
    policy_observation = observation["policy"]

    controller = PositionCommandPID(
      num_envs=env.num_envs,
      device=env.device,
      control_dt=env.step_dt,
      velocity_scale=args_cli.velocity_scale,
    )
    target_position = torch.zeros(env.num_envs, 3, device=env.device)
    target_position[:, 2] = args_cli.hover_height
    target_yaw = torch.zeros(env.num_envs, device=env.device)

    print(
      f"[INFO] Environment ready: num_envs={env.num_envs}, "
      f"device={env.device}, "
      f"physics_dt={env.physics_dt:.3f} s, control_dt={env.step_dt:.3f} s."
    )
    print(
      f"[INFO] policy observation shape={tuple(policy_observation.shape)}, "
      f"action shape=({env.num_envs}, {env.action_manager.total_action_dim})."
    )
    print(
      "[INFO] Observation order: local_position(3), quaternion_wxyz(4), "
      "linear_velocity_w(3), angular_velocity_b(3)."
    )
    print(
      "[INFO] Action order: normalized world velocity(3), "
      "normalized absolute yaw(1)."
    )

    step_count = 0
    tracked_error_sum = 0.0
    tracked_samples = 0
    tracking_start = (
      int(0.75 * args_cli.max_steps) if args_cli.max_steps > 0 else 0
    )
    last_action = torch.zeros(env.num_envs, 4, device=env.device)

    while simulation_app.is_running() and (
      args_cli.max_steps == 0 or step_count < args_cli.max_steps
    ):
      last_action = controller.compute(
        policy_observation, target_position, target_yaw
      )
      observation, _ = env.step(last_action)
      policy_observation = observation["policy"]
      step_count += 1

      if step_count >= tracking_start:
        position_error = torch.linalg.vector_norm(
          policy_observation[:, 0:3] - target_position, dim=-1
        )
        tracked_error_sum += float(position_error.sum().item())
        tracked_samples += env.num_envs

    finite_tensors = (
      torch.isfinite(policy_observation).all()
      and torch.isfinite(last_action).all()
    )
    print(
      f"[INFO] Finished after {step_count} environment steps; "
      f"tensors_finite={bool(finite_tensors)}."
    )
    if tracked_samples > 0:
      mean_error = tracked_error_sum / tracked_samples
      final_error = torch.linalg.vector_norm(
        policy_observation[:, 0:3] - target_position, dim=-1
      )
      print(
        f"[RESULT] mean_position_error_last_quarter={mean_error:.4f} m, "
        f"final_mean={final_error.mean().item():.4f} m, "
        f"final_max={final_error.max().item():.4f} m."
      )
  finally:
    env.close()


if __name__ == "__main__":
  try:
    main()
  finally:
    simulation_app.close(
      skip_cleanup=args_cli.headless or args_cli.max_steps > 0
    )
