# Tutorial 1：ManagerBasedEnv 与 PID Baseline

本篇只增加三个 Manager，把 Tutorial 0 的公共 Scene 包装成可执行
“观察 → 动作 → 仿真”的环境：

```text
外部 CascadedPIDController
    ↓ normalized batch action [N, 4]
ManagerBasedEnv
├── ObservationManager
├── ActionManager
├── EventManager
└── Tutorial 0 的 UavObstacleSceneCfg
```

这里没有 reward、termination、CommandManager、Gym 注册或 RL 算法。PID 位于
`src/isaaclab_uav_tutorial/controllers/`，不是 Environment 的一部分。

## 运行

```bash
# 单环境 GUI
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_01_manager_env_pid.py

# 单环境 headless
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_01_manager_env_pid.py --headless

# 修改固定悬停高度
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_01_manager_env_pid.py --hover_height 0.8
```

脚本仍是独立主入口。`src/` 中只放多个 Tutorial 会复用的 Environment 和 Controller。

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

`action` 是 `[num_envs, 4]`、范围 `[-1, 1]` 的 tensor：

```text
[collective_thrust, roll_moment, pitch_moment, yaw_moment]
```

映射与本机 Isaac Lab 2.3.2 的 Direct Crazyflie 示例一致：

- `collective_thrust=-1` 对应零推力，`+1` 对应 `1.9 × robot_weight`；
- roll、pitch、yaw 力矩（第 1、2、3 维）分别绕 body X、Y、Z 轴施加，
  `±1` 对应 `±0.01 N·m`；
- 推力和力矩通过 `permanent_wrench_composer` 施加到名为 `body` 的 link。

这套 body-wrench 接口可以继续作为后续控制器的低层物理作用接口。未来的
``[v_x, v_y, v_z, yaw]`` 高层动作需要先通过控制器转换为合推力和合力矩，
其中 ``yaw`` 表示期望绝对航向角，而不是期望航向角速度。
具体 ActionTerm 实现在
[`actions/body_wrench.py`](../src/isaaclab_uav_tutorial/actions/body_wrench.py)，
环境配置只负责选择并配置该动作项。

## Reset

EventManager 在 reset 时围绕 Crazyflie 的默认状态施加小幅位置、姿态和速度扰动。
入口只在启动时调用一次完整 reset。后续 RL 教程将由 ``ManagerBasedRLEnv``
根据终止条件自动重置对应的并行环境，不再编写手动局部 reset 演示函数。

固定目标默认是资产初始高度 `[0, 0, 0.5] m`，可用 `--hover_height` 修改。
