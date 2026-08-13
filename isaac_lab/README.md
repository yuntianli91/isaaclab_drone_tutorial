# Isaac Lab UAV RL Tutorial

本项目按照 [ISAACLAB_UAV_RL_CODEX_PLAN.md](docs/ISAACLAB_UAV_RL_CODEX_PLAN.md)
分阶段实现一条连续的无人机强化学习教程。
当前已实现 Tutorial 0 和 **Tutorial 1：ManagerBasedEnv + PID Baseline**；尚未引入
ManagerBasedRLEnv、Gym 或 RL 算法。

## 项目结构

项目采用标准 Python `src/` layout。`scripts/` 中的每个 Tutorial 都是独立主入口；`src/` 只保存
可复用实现。

```text
isaac_lab/
├── README.md
├── pyproject.toml
├── configs/
│   ├── common/
│   │   └── uav_obstacle_base.yaml
│   ├── tasks/
│   │   └── hover_fixed.yaml
│   └── tutorials/
│       └── tutorial1.yaml
├── docs/
├── scripts/
│   ├── plot_flight_csv.py
│   ├── tutorial_00_scene.py
│   └── tutorial_01_manager_env_pid.py
├── src/
│   └── isaaclab_uav_tutorial/
│       ├── config/
│       │   ├── yaml_loader.py
│       │   └── tutorial1.py
│       ├── actions/
│       │   ├── velocity_yaw.py
│       │   └── body_wrench.py
│       ├── assets/
│       │   └── default_uav.py
│       ├── controllers/
│       │   ├── position_command_pid.py
│       │   ├── velocity_yaw.py
│       │   └── attitude.py
│       ├── envs/
│       │   └── hover_manager_env.py
│       ├── monitoring/
│       │   ├── flight_logger.py
│       │   └── flight_plotter.py
│       └── scenes/
│           └── obstacle_scene_cfg.py
└── tests/
```

后续会按实际教学进度增加：

```text
src/isaaclab_uav_tutorial/
├── agents/
├── models/
├── rewards/
├── utils/
└── evaluation/
```

这些目录不会在没有实现内容时用占位 Python 文件提前填充。

## 安装

在仓库根目录将项目以 editable 模式安装到已经配置好的 Isaac Lab 环境：

```bash
conda run -n isaaclab_232 python -m pip install --no-deps -e isaac_lab
```

安装只让独立入口能够导入 `src/` 中的公共代码，不会把 Tutorial 变成模块入口。

## 运行 Tutorial 0

```bash
# 4 个环境 GUI
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_00_scene.py --num_envs 4

# 64 个环境 headless
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_00_scene.py --num_envs 64 --headless
```

脚本默认执行 500 个 physics step 后退出。可使用 `--max_steps 0` 持续运行，直到关闭 Isaac Sim。

详细说明见 [Tutorial 0 文档](docs/tutorial_00_scene.md)。

## 运行 Tutorial 1

```bash
# 使用默认 configs/tutorials/tutorial1.yaml
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_01_manager_env_pid.py

# 选择另一份同结构配置
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_01_manager_env_pid.py \
  --config path/to/tutorial1.yaml
```

入口从
[`configs/tutorials/tutorial1.yaml`](configs/tutorials/tutorial1.yaml)
读取顶层配置。该文件继承公共 UAV/场景配置和固定悬停任务配置，再提供
Tutorial 1 的运行参数和 PID baseline。若将 `velocity_scale` 改为 `null`，入口
会在启动 Isaac Sim 前要求提供明确值。

默认配置会把单环境飞行数据写入
`outputs/flight_logs/tutorial1/<timestamp>/flight.csv`，并在入口结束时直接打开
一个 Matplotlib 分类曲线 Figure，不保存图片。记录开关、环境索引、刷新周期
和绘图开关均位于 `flight_logging` 参数块。

无需启动 Isaac Sim 即可重新打开已有 CSV，便于调试 subplot 布局：

```bash
conda run -n isaaclab_232 python isaac_lab/scripts/plot_flight_csv.py \
  isaac_lab/outputs/flight_logs/tutorial1/<timestamp>/flight.csv
```

详细接口定义见 [Tutorial 1 文档](docs/tutorial_01_manager_env_pid.md)。
