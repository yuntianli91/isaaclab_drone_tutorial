# 实施进度

## Phase 0：本地检查

状态：完成。

### Files changed

- `docs/local_environment.md`

### Commands run

- 检查项目、`AGENTS.md`、规划文件和本地 Isaac Lab 源码；
- 使用 `conda isaaclab_232` 检查 Python、PyTorch、Isaac Sim、skrl 和 Gymnasium；
- 检查 GPU、CUDA、核心 API 与本地示例路径。

### Tests passed

- 本地源码确认为 Isaac Lab v2.3.2；
- Tutorial 0 所需 `AppLauncher`、`InteractiveScene` 和 `CRAZYFLIE_CFG` 均存在；
- PyTorch 可访问 RTX 4090 D。

## Phase 1：Tutorial 0

状态：完成，已迁移为最终 Python project layout。

### 最终结构

- `pyproject.toml`：项目和开发工具配置；
- `scripts/tutorial_00_scene.py`：独立、可直接运行的主入口；
- `src/isaaclab_uav_tutorial/assets/default_uav.py`：默认 UAV；
- `src/isaaclab_uav_tutorial/scenes/obstacle_scene_cfg.py`：公共场景；
- `configs/`：后续 Environment、Agent 和训练配置；
- `docs/tutorial_00_scene.md`：教程说明。

### Commands run

- 对项目 Python 文件运行 Ruff 和无 `.pyc` 编译检查；
- 使用 `--no-deps` 从 `isaac_lab/` 项目根目录执行 editable install；
- 使用独立入口 `python isaac_lab/scripts/tutorial_00_scene.py` 运行全部场景测试；
- 1 environment，headless，20 physics steps；
- 4 environments，GUI，20 physics steps；
- 64 environments，headless，默认 500 physics steps。

### Tests passed

- 静态编译与 Ruff 检查通过；
- 1 environment headless 返回 `exit_code=0`；
- 4 environments GUI 路径返回 `exit_code=0`；
- 64 environments headless 返回 `exit_code=0`；
- 64 环境完成 500 steps，并在 step 200 / 400 批量 reset；
- `env_origins.shape == (num_envs, 3)`；
- `uav_root_pos_w.shape == (num_envs, 3)`；
- reset 后 UAV 相对各自 origin 的位置为 `[0.0, 0.0, 0.5]`；
- Tutorial 0 没有 Manager、Gym 或 RL import。

### Known limitations

- Crazyflie 在 Tutorial 0 中没有控制输入，会受重力下落并在碰撞后翻滚；控制从 Tutorial 1 开始。
- Crazyflie USD 使用 NVIDIA asset root，首次运行依赖网络或已有 cache。
- 自动化只能确认 4 环境 GUI 创建和运行成功；最终视觉布局建议在 `--max_steps 0` 下人工查看。
- 本机 Isaac Sim 5.1.0 的有限步 stage cleanup 会卡住；有限 smoke test 使用官方
  `skip_cleanup=True` 路径退出。

### Next step

Tutorial 0 已作为公共 Scene 被 Tutorial 1 复用。

## Phase 2：Tutorial 1

状态：完成。

### Files changed

- `scripts/tutorial_01_manager_env_pid.py`：独立可执行入口；
- `src/isaaclab_uav_tutorial/actions/body_wrench.py`：可复用的 body-wrench 动作项；
- `src/isaaclab_uav_tutorial/envs/hover_manager_env.py`：ManagerBasedEnv 配置、观测项和 reset event；
- `src/isaaclab_uav_tutorial/controllers/cascaded_pid.py`：环境外部的 Torch batch PID baseline；
- `docs/tutorial_01_manager_env_pid.md`：observation、action、reset 与运行说明；
- `README.md`：结构与 Tutorial 1 入口。

### Tests passed

- Ruff 与 Python 静态编译通过；
- 1 environment、headless、500 environment steps，最终位置误差 `0.0196 m`；
- 4 environments、GUI、100 environment steps，最终平均位置误差 `0.0347 m`；
- 64 environments、headless、500 environment steps，最终平均位置误差 `0.0393 m`，最大误差 `0.1142 m`；
- ObservationManager 输出 `(64, 13)` CUDA tensor；
- ActionManager 接收 `(64, 4)` CUDA tensor；
- 所有最终 observation/action 均为 finite；

### Tutorial boundary

- 复用了 Tutorial 0 的 `UavObstacleSceneCfg`；
- 只引入 ObservationManager、ActionManager 和 EventManager；
- PID 从独立 controller 模块 import，不在 Environment 内；
- 固定目标未放入 observation；
- 未加入 reward、termination、CommandManager、Gym、PPO 或 SKRL。

### Next step

等待用户确认 Tutorial 1 的接口与表现，再开始 Tutorial 2。
