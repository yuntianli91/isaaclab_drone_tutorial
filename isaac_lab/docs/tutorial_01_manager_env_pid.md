# Tutorial 1：ManagerBasedEnv 与 PID Baseline

本篇只增加三个 Manager，把 Tutorial 0 的公共 Scene 包装成可执行
“观察 → 动作 → 仿真”的环境：

```text
外部 PositionCommandPID（Planner baseline）
    ↓ normalized [v_x, v_y, v_z, yaw_absolute]
ManagerBasedEnv
├── ObservationManager
├── ActionManager（唯一 VelocityYawAction）
│   ├── VelocityYawController：velocity/yaw → thrust/attitude
│   ├── AttitudeController：thrust/attitude → body wrench
│   └── BodyWrenchApplier：向 UAV 刚体施力
├── EventManager
└── Tutorial 0 的 UavObstacleSceneCfg
```

这里没有 reward、termination、CommandManager、Gym 注册或 RL 算法。PID 位于
`src/isaaclab_uav_tutorial/controllers/`，不是 Environment 的一部分。

## 运行

```bash
# 单环境 GUI
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_01_manager_env_pid.py \
  --velocity_scale VX_MAX VY_MAX VZ_MAX

# 单环境 headless
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_01_manager_env_pid.py \
  --velocity_scale VX_MAX VY_MAX VZ_MAX --headless

# 修改固定悬停高度
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_01_manager_env_pid.py \
  --velocity_scale VX_MAX VY_MAX VZ_MAX --hover_height 0.8
```

脚本仍是独立主入口。`src/` 中只放多个 Tutorial 会复用的 Environment 和 Controller。
`VX_MAX VY_MAX VZ_MAX` 是三轴最大速度绝对值 (m/s)。这些参数尚未确认，所以入口
要求显式提供，不使用未经确认的经验默认值。

## Observation

`observation["policy"]` 是设备上的 `[num_envs, 13]` tensor，拼接顺序固定为：

| Slice | 含义 | 坐标系 |
|---|---|---|
| `0:3` | UAV 相对各自 environment origin 的位置 | world axes |
| `3:7` | root quaternion，顺序 WXYZ | world |
| `7:10` | root linear velocity | world |
| `10:13` | root angular velocity | body |

固定目标不进入 observation；Tutorial 2 才会引入 CommandManager。

## Action

`action` 是 `[num_envs, 4]`、范围 `[-1, 1]` 的无量纲 tensor：

```text
[v_x, v_y, v_z, yaw_absolute]
```

其中三轴速度位于 world 坐标系；绝对 yaw 位于 world 坐标系，`-1` 和 `+1`
分别映射到 `-π rad` 和 `+π rad`。三轴速度分别乘以命令行提供的
`VX_MAX VY_MAX VZ_MAX`。

环境只注册 `VelocityYawAction`。它先通过速度/航向控制器得到 collective thrust
和期望姿态，再通过姿态控制器得到 body wrench，最后由普通辅助类
`BodyWrenchApplier` 调用 `permanent_wrench_composer`。因此 ActionManager 中不会
同时出现高层动作项和底层 wrench 动作项。

高层 ActionTerm 位于
[`actions/velocity_yaw.py`](../src/isaaclab_uav_tutorial/actions/velocity_yaw.py)，
底层施力辅助类位于
[`actions/body_wrench.py`](../src/isaaclab_uav_tutorial/actions/body_wrench.py)。

## Reset

EventManager 在 reset 时围绕 Crazyflie 的默认状态施加小幅位置、姿态和速度扰动。
入口只在启动时调用一次完整 reset。后续 RL 教程将由 ``ManagerBasedRLEnv``
根据终止条件自动重置对应的并行环境，不再编写手动局部 reset 演示函数。

固定目标默认是资产初始高度 `[0, 0, 1.0] m`，可用 `--hover_height` 修改。
