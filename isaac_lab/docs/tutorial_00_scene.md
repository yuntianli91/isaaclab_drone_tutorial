# Tutorial 0：用 InteractiveScene 创建并行 UAV 场景

## 本篇回答的问题

Isaac Lab 如何声明一个 UAV 场景，并把同一布局复制成多个互不重叠的并行环境？

## 相比上一篇新增了什么

这是起点。本篇只新增：

- `SimulationContext`；
- asset configuration；
- `InteractiveSceneCfg` 与 `InteractiveScene`；
- `{ENV_REGEX_NS}`、`num_envs`、`env_spacing` 和 environment origins；
- scene reset/write/update 与 `sim.step()`。

本篇不包含 Environment、Manager、Gym、PPO 或 SKRL。

## 架构图

```text
UavObstacleSceneCfg（声明）
├── /World/defaultGroundPlane       全局地面
├── /World/Light                    全局灯光
└── {ENV_REGEX_NS}                  每个环境各自的 namespace
    ├── UAV                         Crazyflie
    ├── PillarTall
    ├── PillarMedium
    └── PillarLow
             │
             ▼
InteractiveScene（运行时对象）
├── env_0 @ origin[0]
├── env_1 @ origin[1]
└── ...
```

## 核心类

`UavObstacleSceneCfg` 继承 `InteractiveSceneCfg`，是声明式配置；它描述场景中有什么。
`InteractiveScene` 是运行时对象；它实际生成资产、保存 `env_origins` 并管理批量数据。
二者不能混为一谈。

`assets/default_uav.py` 用 `DEFAULT_UAV_CFG` 适配本地 Isaac Lab v2.3.2 已提供的
`CRAZYFLIE_CFG`；`scenes/obstacle_scene_cfg.py` 负责组合 UAV、地面、灯光和障碍。三个柱体使用
静态、可碰撞的 `CuboidCfg`，在 Tutorial 0～5 中只作为背景，计划到 Tutorial 7～8 再参与感知
和避障。

`DEFAULT_UAV_CFG.init_state` 在项目内显式覆盖初始位置、线速度和角速度；修改
`assets/default_uav.py` 中对应的三个元组即可调整默认起始状态。

默认 `env_spacing=6.0 m`。单个布局中的柱体中心最远约为 1.8 m，尺寸也保留在环境单元内，
因此相邻 clone 的障碍不会重叠。

## 执行链

```text
AppLauncher
  ↓
SimulationContext
  ↓
UavObstacleSceneCfg(num_envs, env_spacing)
  ↓
InteractiveScene
  ↓
sim.reset()
  ↓
UAV world position = configured local position + scene.env_origins
  ↓
scene.write_data_to_sim()
  ↓
sim.step()
  ↓
scene.update(physics_dt)
```

Crazyflie 在本篇没有控制器或推力输入，因此会在重力下落到地面。这是预期行为，不代表悬停
控制已经实现。脚本周期性恢复初始状态，只用于持续观察场景与克隆是否正确；控制接口属于
Tutorial 1。

## 如何运行

首次运行前，在仓库根目录安装项目的 `src/` 公共代码：

```bash
conda run -n isaaclab_232 python -m pip install --no-deps -e isaac_lab
```

然后直接运行独立 Tutorial 入口：

```bash
# 1 个环境 smoke test
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_00_scene.py \
  --num_envs 1 --headless --max_steps 50

# 4 个环境 GUI
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_00_scene.py \
  --num_envs 4

# 64 个环境 headless
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_00_scene.py \
  --num_envs 64 --headless
```

默认运行 500 个 physics step 后退出。若希望 GUI 一直运行：

```bash
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_00_scene.py \
  --num_envs 4 --max_steps 0
```

本机 Isaac Sim 5.1.0 在有限步运行后优雅关闭包含远程 Crazyflie asset 的 stage 时会卡在 cleanup。
因此脚本在 headless 或 `--max_steps > 0` 时使用本地 API 明确提供的 `skip_cleanup=True`
immediate-exit 路径；`--max_steps 0` 的 GUI 交互模式仍执行完整关闭流程。这不改变 physics step
或 scene 数据验证。

本地 `CRAZYFLIE_CFG` 的 USD 位于 NVIDIA asset root。首次运行需要网络可达，或者机器上已经有
对应 cache。

## 预期输出

控制台会输出：

```text
env_origins.shape=(num_envs, 3)
uav_root_pos_w.shape=(num_envs, 3)
```

并打印前四个环境的 origin，以及 UAV 相对各自 origin 的位置。后者应均接近
`[0.0, 0.0, 0.5]`。GUI 中每个环境应有一架 UAV、相同的三根柱体布局和共享地面；相邻布局
不应重叠。

## 验收标准

- 1、4、64 个环境均能完成指定 physics steps；
- `scene.env_origins` 是 `[num_envs, 3]` batch；
- reset 后 UAV 的 local position 在所有环境中一致；
- UAV 和柱体均使用 `{ENV_REGEX_NS}`；
- 不含 Manager 或 RL 代码。

## 常见误解

- `InteractiveSceneCfg` 是配置，不是运行时 scene。
- `{ENV_REGEX_NS}` 负责把每环境资产绑定到对应 namespace；它不是手工字符串拼接的环境编号。
- `root_pos_w` 是 world frame，reset 到每个 clone 时必须加 `scene.env_origins`。
- 并行 scene 不是 RL environment；本篇没有 observation、action、reward 或 episode。
- UAV 下落是因为本篇刻意没有控制器，不是资产克隆失败。

## 下一篇为什么自然出现

现在已经能批量生成相同的 UAV 世界，但还没有统一的“观察—动作—推进”接口。Tutorial 1 将在
同一 scene 之上引入 `ManagerBasedEnv` 的 Observation、Action 与 reset Event，并由环境外部的
PID baseline 验证控制接口。
