# 本地环境检查

检查日期：2026-08-07  
目标环境：`conda isaaclab_232`

## 项目状态

开始 Tutorial 0 前，`isaac_lab/` 中只有 `ISAACLAB_UAV_RL_CODEX_PLAN.md`：

- 不是现成的 Isaac Lab external project；
- 没有 `pyproject.toml`、`setup.py` 或 `source/`；
- 没有已有 UAV / RL 实现；
- 仓库根目录存在并已遵守 `AGENTS.md`；
- 仓库根目录的 `.git/` 是空目录，因此当前目录不能执行 Git 状态检查。

实施规格最初没有给出公共源码名称，用户随后确认使用 `isaaclab_uav_tutorial`。项目最终采用标准
Python `src/` layout：根目录 `pyproject.toml` 管理项目，公共代码位于
`src/isaaclab_uav_tutorial/`，独立 Tutorial 主入口位于 `scripts/`。不使用 Isaac Lab extension 的
`source/<extension>/config/extension.toml` 结构。

## 版本与硬件

| 项目 | 本机结果 |
|---|---|
| Isaac Lab source | `v2.3.2-dirty`，revision `37ddf626871758333d6ed89cf64ad702aef127d0` |
| Isaac Lab editable package metadata | `0.54.2` |
| Isaac Sim | `5.1.0.0` |
| Python | `3.11.15` |
| PyTorch | `2.7.0+cu128` |
| PyTorch CUDA runtime | `12.8` |
| CUDA available | `True`（沙箱外 GPU 检查） |
| GPU | NVIDIA GeForce RTX 4090 D，24564 MiB |
| NVIDIA driver | `580.159.03` |
| skrl | `2.1.0` |
| Gymnasium | `1.2.1` |

说明：源码根目录的 `VERSION` 和 Git tag 均为 `2.3.2`；`isaaclab` Python distribution 的
editable package metadata 显示 `0.54.2`。两者如实记录，不把它们强行解释为同一种版本号。

## 核心 API 存在性

已在本地 Isaac Lab 源码中确认以下对象存在：

| 对象 | 本地源码 |
|---|---|
| `InteractiveScene` / `InteractiveSceneCfg` | `source/isaaclab/isaaclab/scene/` |
| `ManagerBasedEnv` / `ManagerBasedEnvCfg` | `source/isaaclab/isaaclab/envs/manager_based_env*.py` |
| `ManagerBasedRLEnv` / `ManagerBasedRLEnvCfg` | `source/isaaclab/isaaclab/envs/manager_based_rl_env*.py` |
| `DirectRLEnv` / `DirectRLEnvCfg` | `source/isaaclab/isaaclab/envs/direct_rl_env*.py` |
| `ActionManager` | `source/isaaclab/isaaclab/managers/action_manager.py` |
| `ObservationManager` | `source/isaaclab/isaaclab/managers/observation_manager.py` |
| `EventManager` | `source/isaaclab/isaaclab/managers/event_manager.py` |
| `CommandManager` | `source/isaaclab/isaaclab/managers/command_manager.py` |
| `RewardManager` | `source/isaaclab/isaaclab/managers/reward_manager.py` |
| `TerminationManager` | `source/isaaclab/isaaclab/managers/termination_manager.py` |
| `CurriculumManager` | `source/isaaclab/isaaclab/managers/curriculum_manager.py` |
| `SkrlVecEnvWrapper` | `source/isaaclab_rl/isaaclab_rl/skrl.py`（本版本中是函数，不是类） |

上表中的相对路径均相对于本机 Isaac Lab 源码根目录
`/home/yuntian/isaac_lab/IsaacLab`。

## 本地参考实现

后续只把这些文件作为本版本 API 参考，不复制其任务结构：

| 用途 | 本地文件 |
|---|---|
| `InteractiveScene` | `scripts/tutorials/02_scene/create_scene.py` |
| `ManagerBasedEnv` | `source/isaaclab/test/envs/check_manager_based_env_floating_cube.py` |
| `ManagerBasedRLEnv` | `source/isaaclab_tasks/isaaclab_tasks/manager_based/drone_arl/track_position_state_based/config/arl_robot_1/track_position_state_based_env_cfg.py` |
| `DirectRLEnv` | `source/isaaclab_tasks/isaaclab_tasks/direct/quadcopter/quadcopter_env.py` |
| Gym registration | `source/isaaclab_tasks/isaaclab_tasks/direct/quadcopter/__init__.py` |
| SKRL PPO training entry | `scripts/reinforcement_learning/skrl/train.py` |
| SKRL PPO UAV config | `source/isaaclab_tasks/isaaclab_tasks/manager_based/drone_arl/track_position_state_based/config/arl_robot_1/agents/skrl_ppo_cfg.yaml` |
| Camera | `scripts/tutorials/04_sensors/run_usd_camera.py` |
| RayCaster / LiDAR-like rays | `scripts/tutorials/04_sensors/run_ray_caster.py` |
| Crazyflie asset | `source/isaaclab_assets/isaaclab_assets/robots/quadcopter.py` |

## Tutorial 0 采用的本地事实

- 使用本地 `isaaclab_assets.CRAZYFLIE_CFG`；其 USD 指向 Isaac asset root 下的
  `Robots/Bitcraze/Crazyflie/cf2x.usd`。
- 使用本版本 `AppLauncher` 启动顺序：先解析 launcher 参数并启动 app，再 import Isaac Lab
  scene/sim/asset 模块。
- 使用 `{ENV_REGEX_NS}` 复制 UAV 和静态柱体。
- world-frame UAV root state 在 reset 时显式加上 `scene.env_origins`。
- 本机 Isaac Sim 5.1.0 在有限步运行结束后优雅关闭远程 asset stage 时会停在 stage cleanup；
  脚本在 headless 或 `--max_steps > 0` 的有限 smoke test 中使用
  `SimulationApp.close(skip_cleanup=True)` 的官方 immediate-exit 路径。`--max_steps 0` 的交互运行
  GUI 仍执行完整 cleanup。
- 本机 `CRAZYFLIE_CFG` 指向 NVIDIA S3 asset root；首次运行需要能访问该 asset，后续可使用本地
  cache。测试时远程 `cf2x.usd` 及其依赖均成功打开。
