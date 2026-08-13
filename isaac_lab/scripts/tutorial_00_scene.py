"""Tutorial 0：使用 :class:`InteractiveScene` 创建并复制 UAV 场景。

本文件是独立可执行入口，只介绍仿真、资产和场景，不包含环境 Manager 或
RL。
"""

# AppLauncher 必须先启动 Isaac Sim，之后才能导入仿真模块。
# ruff: noqa: E402

from __future__ import annotations

import argparse

from isaaclab.app import AppLauncher

parser_description = "Create parallel Crazyflie scenes with static pillars."
parser = argparse.ArgumentParser(description=parser_description)
parser.add_argument("--num_envs", type=int, default=4,
                    help="Number of parallel scenes to create.")
parser.add_argument("--env_spacing", type=float, default=6.0,
                    help="Distance in metres between neighbouring "
                         "environment origins.")
parser.add_argument("--max_steps", type=int, default=500,
                    help="Number of physics steps before exit; use 0 to run "
                         "until the app closes.")
parser.add_argument("--reset_interval", type=int, default=200,
                    help="Physics steps between UAV state resets; use 0 to "
                         "disable periodic resets.")
AppLauncher.add_app_launcher_args(parser)
args_cli = parser.parse_args()

if args_cli.num_envs < 1:
  parser.error("--num_envs must be at least 1")
if args_cli.env_spacing <= 0.0:
  parser.error("--env_spacing must be positive")
if args_cli.max_steps < 0:
  parser.error("--max_steps must be non-negative")
if args_cli.reset_interval < 0:
  parser.error("--reset_interval must be non-negative")

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app


# AppLauncher 启动应用后，立即导入 Isaac Lab 和项目仿真模块。
import isaaclab.sim as sim_utils
from isaaclab.assets import Articulation
from isaaclab.scene import InteractiveScene
from isaaclab.sim import SimulationContext

from isaaclab_uav_tutorial.scenes import UavObstacleSceneCfg


# ===== reset_uavs =========================================================== #
def reset_uavs(scene: InteractiveScene) -> None:
  """将所有 UAV 恢复到各自环境原点附近的配置状态。

  Args:
    scene: 包含批量 UAV 资产的交互场景。
  """
  uav: Articulation = scene["uav"]

  root_state = uav.data.default_root_state.clone()
  root_state[:, :3] += scene.env_origins
  uav.write_root_pose_to_sim(root_state[:, :7])
  uav.write_root_velocity_to_sim(root_state[:, 7:])
  uav.write_joint_state_to_sim(uav.data.default_joint_pos,
                               uav.data.default_joint_vel)
  scene.reset()


# ===== print_scene_state ==================================================== #
def print_scene_state(scene: InteractiveScene) -> None:
  """输出批量 UAV 初始状态和环境原点。

  Args:
    scene: 包含批量 UAV 资产的交互场景。
  """
  uav: Articulation = scene["uav"]
  local_positions = uav.data.root_pos_w - scene.env_origins
  preview_count = min(scene.cfg.num_envs, 4)

  print(f"[INFO] env_origins.shape={tuple(scene.env_origins.shape)}")
  print(f"[INFO] uav_root_pos_w.shape={tuple(uav.data.root_pos_w.shape)}")
  print(f"[INFO] first {preview_count} environment origins:\n"
        f"{scene.env_origins[:preview_count]}")
  print(f"[INFO] first {preview_count} UAV positions relative to origins:\n"
        f"{local_positions[:preview_count]}")


# ===== run_simulator ======================================================== #
def run_simulator(sim: SimulationContext, scene: InteractiveScene) -> None:
  """推进物理仿真，并按指定周期恢复 UAV 初始状态。

  Args:
    sim: Isaac Lab 仿真上下文。
    scene: 包含批量 UAV 资产的交互场景。
  """
  physics_dt = sim.get_physics_dt()
  step_count = 0

  while simulation_app.is_running() and (
    args_cli.max_steps == 0 or step_count < args_cli.max_steps
  ):
    if (
      args_cli.reset_interval > 0
      and step_count > 0
      and step_count % args_cli.reset_interval == 0
    ):
      reset_uavs(scene)
      print(f"[INFO] Reset all UAVs at physics step {step_count}.")

    scene.write_data_to_sim()
    sim.step()
    scene.update(physics_dt)
    step_count += 1

  print(f"[INFO] Finished after {step_count} physics steps.")


# ===== main ================================================================= #
def main() -> None:
  """创建仿真上下文和经过复制的交互场景。"""
  sim_cfg = sim_utils.SimulationCfg(dt=0.01, device=args_cli.device)
  sim = SimulationContext(sim_cfg)
  sim.set_camera_view(eye=(9.0, 9.0, 7.0), target=(0.0, 0.0, 0.8))

  scene_cfg = UavObstacleSceneCfg(num_envs=args_cli.num_envs,
                                  env_spacing=args_cli.env_spacing,
                                  replicate_physics=True)
  scene = InteractiveScene(scene_cfg)

  sim.reset()
  reset_uavs(scene)
  scene.update(sim.get_physics_dt())

  print(f"[INFO] Scene ready: num_envs={scene.cfg.num_envs}, "
        f"env_spacing={scene.cfg.env_spacing:.2f} m, device={sim.device}.")
  print_scene_state(scene)
  run_simulator(sim, scene)


if __name__ == "__main__":
  try:
    main()
  finally:
    # 本机 Isaac Sim 5.1.0 在有限运行后清理远程资产 Stage 时会卡住。
    # 有限 smoke test 使用立即退出路径；交互 GUI 仍执行完整清理。
    skip_cleanup = args_cli.headless or args_cli.max_steps > 0
    simulation_app.close(skip_cleanup=skip_cleanup)
