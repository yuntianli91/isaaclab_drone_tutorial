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
# 使用默认 configs/tutorials/tutorial1.yaml
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_01_manager_env_pid.py

# 选择另一份同结构 YAML
conda run -n isaaclab_232 python isaac_lab/scripts/tutorial_01_manager_env_pid.py \
  --config path/to/tutorial1.yaml
```

脚本仍是独立主入口。除了可选的 `--config` 路径外，不接收 Tutorial 或
AppLauncher 参数；所有数值和运行模式统一在 YAML 中维护。

## Configuration

Tutorial 1 默认读取 `configs/tutorials/tutorial1.yaml`。顶层配置依次合并：

```text
common/uav_obstacle_base.yaml
    ↓
tasks/hover_fixed.yaml
    ↓
tutorials/tutorial1.yaml
```

三层 YAML 共同提供以下具体值：

- 并行环境数量、间距、运行步数和随机种子；
- Isaac Sim 的 headless、device、livestream、camera 和 rendering mode；
- 仿真周期、decimation、渲染周期、重力和纹理等待设置；
- viewer 位置和注视点；
- UAV 初始位置、WXYZ 姿态、线速度和角速度；
- 灯光以及三根柱体的位置、尺寸、颜色和粗糙度；
- ObservationManager 的可序列化选项；
- reset 位姿扰动与速度扰动范围；
- 固定悬停高度和绝对目标航向；
- Action 使用的 `asset_name`、`body_name` 和 `velocity_scale`；
- 三层传统控制器参数；
- 单环境 FlightLogger 的启用状态、环境索引、输出目录、刷新周期和绘图开关。

`class_type` 和 Manager 使用的 Python 函数仍留在 `Cfg` 类中。YAML 的
`velocity_scale` 位于顶层 Tutorial 配置中。若将其显式改为 `null`，该值会被
加载为 Python `None`，入口会在启动 Isaac Sim 前报告配置缺失。
其他顶层配置文件可通过 `--config PATH` 选择。

公共加载逻辑位于 `config/yaml_loader.py`，支持相对 `base` 路径、递归
mapping 合并、scalar/list 覆盖和循环引用检测。Tutorial 1 的参数模型位于
`config/tutorial1.py`。后续 Tutorial 可以复用稳定配置和加载逻辑，只增加
各自的顶层覆盖、参数模型和环境装配函数。

## Observation

`observation["policy"]` 是设备上的 `[num_envs, 13]` tensor，拼接顺序固定为：

| Slice | 含义 | 坐标系 |
|---|---|---|
| `0:3` | UAV 位置 | E |
| `3:7` | B 系相对于 E 系的四元数，顺序 WXYZ | EB |
| `7:10` | root linear velocity | E |
| `10:13` | root angular velocity | body |

固定目标不进入 observation；Tutorial 2 才会引入 CommandManager。

## Action

`action` 是 `[num_envs, 4]`、范围 `[-1, 1]` 的无量纲 tensor：

```text
[v_x, v_y, v_z, yaw_absolute]
```

其中三轴速度位于 E 系；绝对 yaw 以 E 系为参考，`-1` 和 `+1`
分别映射到 `-π rad` 和 `+π rad`。三轴速度分别乘以 YAML 中的
`velocity_scale`。

环境只注册 `VelocityYawAction`。它先通过速度/航向控制器得到 collective thrust
和期望姿态，再通过姿态控制器得到 body wrench，最后由普通辅助类
`BodyWrenchApplier` 调用 `permanent_wrench_composer`。因此 ActionManager 中不会
同时出现高层动作项和底层 wrench 动作项。

高层 ActionTerm 位于
[`actions/velocity_yaw.py`](../src/isaaclab_uav_tutorial/actions/velocity_yaw.py)，
底层施力辅助类位于
[`actions/body_wrench.py`](../src/isaaclab_uav_tutorial/actions/body_wrench.py)。

## Flight log

`FlightLogger` 面向单环境 demo 和飞行效果评估。虽然环境内部仍使用 batch
tensor，但 Logger 只从 `flight_logging.env_id` 指定的 environment 提取一条
轨迹。每个 physics step 写入一行。

CSV 固定记录以下内容：

- `simulation_time_s` 和 `env_id`；
- E 系位置、EB 四元数、E 系线速度和 B 系角速度；
- 物理单位的 E 系期望速度和绝对期望 yaw；
- collective thrust、期望 EB 四元数和 B 系合力矩。

CSV 不保存 ObservationManager 输出、归一化 action、Euler 角或 step number。
ActionTerm 在每个 physics interval 起点缓存状态、保持的高层指令和本次内环
输出；每次 `env.step()` 返回后再批量写入该 decimation 区间的数据。

导航数据统一采用 environment frame `E`，机体系数据保留在 body frame `B`。
当前各 environment 只相对 `W` 平移，但实现仍使用完整变换：

```text
p_E = R_EW (p_W - p_WE)
v_E = R_EW v_W
R_EB = R_EW R_WB
```

当前 `R_EW = I`，`p_WE = env_origin_W`。

退出入口后，`FlightPlotter` 可根据 CSV 直接打开一个 Matplotlib 分类曲线
Figure。
Euler 角只在绘图时由四元数临时计算，不写入 CSV，也不保存 PNG。默认输出
位置只有 CSV：

单个 Figure 包含位置、RPY 姿态、线速度、角速度、collective thrust 和力矩
subplot。Figure 采用两列布局：左列依次为 X/Y/Z 位置、roll/pitch/yaw 姿态和
collective thrust；右列依次为 X/Y/Z 线速度、X/Y/Z 角速度和 X/Y/Z 力矩。
线速度和 RPY 姿态在对应轴内对比 actual 与 desired。四元数和 B 系合力不直接
绘制，也不记录 B 系合力。所有 legend 固定在右上角，subplot 使用 constrained
layout 随 Figure 窗口尺寸自动缩放和重新布局。

```text
outputs/flight_logs/tutorial1/<timestamp>/
└── flight.csv
```

调试绘图格式时，可以直接读取已有 CSV，不需要启动 Isaac Sim：

```bash
conda run -n isaaclab_232 python isaac_lab/scripts/plot_flight_csv.py \
  isaac_lab/outputs/flight_logs/tutorial1/<timestamp>/flight.csv
```

该功能与后续多环境 RL 训练指标的 W&B 记录分离；FlightLogger 不负责 reward、
episode 或 loss。

## Reset

EventManager 在 reset 时围绕 Crazyflie 的默认状态施加小幅位置、姿态和速度扰动。
入口只在启动时调用一次完整 reset。后续 RL 教程将由 ``ManagerBasedRLEnv``
根据终止条件自动重置对应的并行环境，不再编写手动局部 reset 演示函数。

公共 UAV 配置中的初始位置是 `[0, 0, 0.1] m`；固定悬停任务配置中的
目标高度是 `1.0 m`。顶层 Tutorial 配置也可以显式覆盖这些值。
