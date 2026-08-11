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
├── docs/
├── scripts/
│   ├── tutorial_00_scene.py
│   └── tutorial_01_manager_env_pid.py
├── src/
│   └── isaaclab_uav_tutorial/
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
# 单环境 GUI，显式设置 world XYZ 最大速度 (m/s)
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_01_manager_env_pid.py \
  --velocity_scale VX_MAX VY_MAX VZ_MAX

# 单环境 headless
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_01_manager_env_pid.py \
  --velocity_scale VX_MAX VY_MAX VZ_MAX --headless
```

这里没有替三轴速度上限设置经验默认值；确认实际限制后可再固化到配置中。

详细接口定义见 [Tutorial 1 文档](docs/tutorial_01_manager_env_pid.md)。
