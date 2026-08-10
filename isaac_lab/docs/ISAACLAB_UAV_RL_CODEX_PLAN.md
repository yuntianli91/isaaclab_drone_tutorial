# Isaac Lab UAV Reinforcement Learning Tutorial — Codex 实施规格

> 本文档是给本地 Codex CLI 的工程实施说明。  
> 目标不是复刻 Isaac Lab 官方 Tutorial 的章节结构，而是构建一条**连续、递进、面向无人机强化学习研究**的学习路线。  
> 所有 Tutorial 应围绕同一套四旋翼场景和任务逐步演化，尽可能复用代码，让读者能够清楚看到每一步“新增了什么”。

---

## 0. 总体任务

请在当前项目中实现一套 Isaac Lab UAV RL Tutorial，主线如下：

```text
Tutorial 0  Parallel Simulation / InteractiveScene
    ↓
Tutorial 1  ManagerBasedEnv / Sense–Act / PID Baseline
    ↓
Tutorial 2  ManagerBasedRLEnv / Fixed-Goal RL Task
    ↓
Tutorial 3  DirectRLEnv / Same Task, Different Workflow
    ↓
Tutorial 4  Gym Registration / Env Config / RL Wrapper
    ↓
Tutorial 5  SKRL + PPO / Goal-Conditioned Policy
    ↓
Tutorial 6  Custom UAV Asset
    ↓
Tutorial 7  Camera / Stereo / LiDAR Sensors
    ↓
Tutorial 8  Goal-Conditioned Obstacle Navigation
```

### 核心教学原则

1. **始终使用同一条无人机任务主线。**
   - 不要在不同 Tutorial 中切换 Cartpole、Ant、ANYmal、机械臂等无关对象。
   - 默认使用 Isaac Lab 自带、可直接运行的轻量级四旋翼模型（优先使用本地版本已有的 Crazyflie / quadrotor 配置；实际名称以本地安装版本为准）。

2. **每个 Tutorial 只新增 1～2 个主要抽象。**
   - 新代码必须建立在前一 Tutorial 的代码和概念之上。
   - 避免单篇同时引入 Scene、Manager、Gym、PPO、Sensor 等多个大主题。

3. **区分四个层级。**
   ```text
   Asset       = 机器人/物体是什么
   Scene       = 世界里有什么
   Environment = Agent 如何与世界交互、任务如何定义
   Agent       = 用什么算法学习/控制
   ```

4. **PID 不是教学主体。**
   - PID 只作为传统控制 baseline。
   - 将完整 PID 控制器实现放到独立工具模块中。
   - Tutorial 正文只 import 和调用，不展开 PID 推导。

5. **CommandManager 不等于 GCRL。**
   - CommandManager 负责生成、维护和更新任务目标/参考量 `g`。
   - 固定点悬停：Command 始终为固定值。
   - Goal-conditioned RL：Command 可以从 goal distribution 中采样。
   - 真正使 policy 成为 Goal-Conditioned Policy 的关键，是**goal 信息进入 policy observation**：
     ```text
     π(a | s)     → 普通 fixed-goal policy
     π(a | s, g)  → goal-conditioned policy
     ```

6. **Manager-Based 和 Direct 必须实现同一个任务。**
   - Tutorial 3 不重新设计 reward、observation、reset、action 或目标。
   - 唯一主要变化是软件组织方式。

7. **以本地 Isaac Lab 版本为准。**
   - 不假设最新网页文档 API 与本地版本一致。
   - 在修改代码前先检查本地安装、版本和现有示例。
   - 优先复用当前版本实际存在的类、Config、ActionTerm、Sensor API 和训练入口。
   - 若本地版本使用 `scripts/reinforcement_learning/skrl/train.py`，沿用该方式。
   - 若本地版本已经采用新的 `isaaclab train` / `uv run isaaclab ...` CLI，则遵循本地版本推荐方式。
   - 不为了追求最新版 API 而升级用户环境。

---

# 1. 执行前置检查

Codex 在写任何 Tutorial 前，先完成以下检查，并记录到 `docs/local_environment.md`。

## 1.1 检查项目

确认：

- 当前工作目录结构；
- 是否已经是 Isaac Lab external project；
- 是否已经有 `pyproject.toml`、`setup.py`、`source/` 等结构；
- 是否存在已有 UAV / RL 代码；
- 是否有 `AGENTS.md`，若存在必须遵守。

不要无理由重建项目。

## 1.2 检查 Isaac Lab

确认至少以下内容：

```text
Isaac Lab version / git revision
Isaac Sim version
Python version
PyTorch version
CUDA availability
skrl version
Gymnasium version
```

并检查本地源码/包中是否存在：

```text
InteractiveScene
InteractiveSceneCfg

ManagerBasedEnv
ManagerBasedEnvCfg

ManagerBasedRLEnv
ManagerBasedRLEnvCfg

DirectRLEnv
DirectRLEnvCfg

ActionManager
ObservationManager
EventManager
CommandManager
RewardManager
TerminationManager
CurriculumManager

SkrlVecEnvWrapper
```

## 1.3 找到本地参考实现

只把本地 Isaac Lab 示例当作 **API 参考**，不要复制其混乱教学结构。

至少定位：

- 一个 `InteractiveScene` 示例；
- 一个 `ManagerBasedEnv` 示例；
- 一个 `ManagerBasedRLEnv` 示例；
- 一个 `DirectRLEnv` 示例；
- 一个 Gym registration 示例；
- 一个 SKRL PPO 训练任务；
- 一个 Camera 示例；
- 一个 RayCaster / LiDAR 相关示例；
- 一个四旋翼/无人机资产配置。

将实际文件路径记录进 `docs/local_environment.md`。

---

# 2. 推荐工程结构

优先采用下面的结构；如果现有 external project 已经有标准结构，则在不破坏包结构的情况下等价映射。

```text
isaac_lab/
├── README.md
├── pyproject.toml
├── .gitignore
├── configs/
│   └── README.md
├── scripts/
│   └── tutorial_00_scene.py
├── src/
│   └── isaaclab_uav_tutorial/
│       ├── __init__.py
│       ├── assets/
│       │   └── default_uav.py
│       └── scenes/
│           └── obstacle_scene_cfg.py
├── tests/
│   └── README.md
└── docs/
```

### 目录职责必须明确

```text
assets/
    定义“机器人是什么”

scenes/
    定义“世界里有什么”

mdp/
    定义 observation / reward / command / reset 等任务函数

tasks/
    组合一个完整的 RL Task

agents/
    定义 PPO / 网络 / 优化器等训练参数

tools/controllers/
    保存 PID 等非教学主体工具

tutorials/
    提供每一步最小、可直接运行的演示入口

docs/
    解释每一步为什么这样设计
```

---

# 3. 全系列公共场景设计

所有 Tutorial 使用同一个基础场景。

## 3.1 场景

每个并行环境至少包含：

- 一架轻量级四旋翼；
- 地面；
- 若干根高低不同的静态柱体；
- 基础灯光；
- 足够的环境间距，避免 clone 之间发生物理交互。

示意：

```text
┌────────────────────────────┐
│                 Goal       │
│                  ★         │
│        █                   │
│        █       ███         │
│ UAV    █       ███     █   │
│  ◇             ███     █   │
└────────────────────────────┘
```

### 注意

Tutorial 0～5 的悬停任务中，柱子可以只是环境背景，不必强行参与 reward。

它们会在 Tutorial 7～8 中用于：

- LiDAR / RayCaster 感知；
- obstacle avoidance；
- goal-conditioned navigation。

这样 Tutorial 0 建立的场景资产在后续真正被复用。

---

# 4. Tutorial 0 — Parallel Simulation with InteractiveScene

## 4.1 教学目标

回答：

> Isaac Lab 如何创建一个场景，并把它复制成大量并行环境？

只讲 Simulation / Asset / Scene。

**本 Tutorial 不引入 Environment 和 RL 概念。**

## 4.2 新增概念

- `SimulationContext`
- `InteractiveSceneCfg`
- `InteractiveScene`
- asset configuration
- environment cloning
- `num_envs`
- `env_spacing`
- environment origins
- `{ENV_REGEX_NS}` 或本地版本等价机制
- scene reset / write / update
- `sim.step()`

## 4.3 禁止事项

不要出现：

- ActionManager
- ObservationManager
- RewardManager
- CommandManager
- Gym registration
- PPO
- SKRL

## 4.4 演示

至少提供：

```bash
tutorial_00_scene.py --num_envs 4
tutorial_00_scene.py --num_envs 64 --headless
```

实际参数形式以项目现有 AppLauncher 规范为准。

程序应做到：

- 生成多环境；
- 每个环境有一架 UAV 和相同柱子布局；
- 能观察 UAV 的初始状态；
- 可执行若干 physics step；
- 不发生明显跨环境碰撞。

## 4.5 验收

- [ ] 1 个环境可运行；
- [ ] 4 个环境可视化正确；
- [ ] 64 个环境 headless 可运行；
- [ ] environment origin 使用正确；
- [ ] 没有 Manager 或 RL 代码混入。

---

# 5. Tutorial 1 — ManagerBasedEnv + PID Baseline

## 5.1 教学目标

回答：

> 如何把 Scene 包装成 Agent 可以“观察 → 给动作 → 推进仿真”的环境？

使用：

```text
ManagerBasedEnv
├── InteractiveScene
├── ObservationManager
├── ActionManager
└── EventManager
```

## 5.2 PID 的定位

PID 是外部 Agent / Controller：

```text
Observation
    ↓
Imported Cascaded PID
    ↓
Action
    ↓
ManagerBasedEnv
```

不要把 PID 实现嵌入 Env。

建议：

```python
from ...tools.controllers.cascaded_pid import CascadedPIDController
```

PID 只负责产生和 RL policy 相同语义的 action。

## 5.3 Action 设计

优先采用对后续 RL 有复用价值的控制接口。

例如：

```text
action =
[
    collective_thrust,
    roll_control,
    pitch_control,
    yaw_control
]
```

具体采用 body wrench、thrust/moment 或本地 multirotor action term，以本地 Isaac Lab UAV API 为准。

要求：

- action normalized / physical scaling 定义清楚；
- PID 与 RL 使用同一 action interface；
- 不允许 Tutorial 1 用一种 action，而 Tutorial 5 完全换另一种 action，除非有明确必要性。

## 5.4 Observation

先使用纯 state-based observation，例如：

```text
root orientation / projected gravity
linear velocity
angular velocity
position or position-related state
```

此阶段目标固定，因此不要求把 goal 放入 observation。

## 5.5 EventManager

至少演示 reset event，例如：

- 初始位置微扰；
- 初始姿态微扰；
- 初始线速度 / 角速度归零或随机小扰动。

不要在这一篇展开复杂 domain randomization。

## 5.6 固定悬停目标

PID baseline 固定目标：

```text
g0 = [0, 0, hover_height]
```

此目标可以由 controller 参数提供；RL 环境中的 CommandManager 到 Tutorial 2 再正式引入。

## 5.7 验收

- [ ] `ManagerBasedEnv` 正常初始化；
- [ ] ObservationManager 输出 batch tensor；
- [ ] ActionManager 能实际控制 UAV；
- [ ] Event reset 对指定 env 生效；
- [ ] PID 从环境外部 import；
- [ ] PID 能在 1 个环境实现基本悬停；
- [ ] PID 能对多个并行环境产生 batch action；
- [ ] PID 代码和 Isaac Lab 教学代码解耦。

---

# 6. Tutorial 2 — ManagerBasedRLEnv + Fixed-Goal RL Task

## 6.1 教学目标

回答：

> 如何把一个普通 sense–act environment 变成完整 RL Task？

从：

```text
ManagerBasedEnv
```

扩展到：

```text
ManagerBasedRLEnv
├── Scene
├── Action
├── Observation
├── Event
├── Command
├── Reward
├── Termination
└── Curriculum
```

## 6.2 最重要的设计：CommandManager 先管理固定目标

本 Tutorial **不是 GCRL**。

CommandManager 的作用是把目标从 reward 逻辑中解耦：

```text
CommandManager
    ↓
fixed command g0 = [0, 0, hover_height]
    ↓
RewardManager 使用 g0
```

不要在 reward 函数中硬编码目标点。

### Fixed command

Command 始终返回：

```text
g = g0
```

不做 goal distribution 采样。

## 6.3 Observation 仍为普通 state observation

Tutorial 2 保持：

```text
π(a | s)
```

而不是：

```text
π(a | s, g)
```

即：

- CommandManager 存在；
- Reward 知道 target；
- policy observation **不必包含 goal**。

原因：

固定目标只有一个，policy 不需要区分不同目标。

这样 Tutorial 5 才能清晰展示“普通固定目标 RL → Goal-Conditioned RL”到底改变了什么。

## 6.4 RewardManager

建议最少包含：

```text
position_tracking
attitude_stability
linear_velocity_penalty
angular_velocity_penalty
action_rate_penalty
```

不要追求复杂 reward shaping。

所有 target-dependent reward 必须读取 CommandManager 的 command，而不是使用重复常量。

## 6.5 TerminationManager

至少考虑：

```text
timeout
crash / altitude too low
excessive tilt
out of workspace
```

区分：

```text
terminated
truncated
```

## 6.6 CurriculumManager

只用一个简单 curriculum 演示机制。

推荐：

```text
initial pose disturbance
small → medium → large
```

此处不要使用 goal-space curriculum，因为 goal 仍然固定。

Tutorial 5 再把 Curriculum 用于扩大 goal distribution。

## 6.7 教学重点

明确说明：

```text
CommandManager:
    “目标是什么 / 如何维护目标”

ObservationManager:
    “policy 能看到什么”

RewardManager:
    “相对于目标做得怎么样”
```

并明确：

> 使用 CommandManager 并不自动意味着 GCRL。

## 6.8 验收

- [ ] Fixed Command 工作；
- [ ] Reward 从 Command 读取 target；
- [ ] Observation 中没有为了“预埋”而强行加入随机 goal；
- [ ] Reward / Termination 分项日志可观察；
- [ ] Curriculum 能修改一个简单难度参数；
- [ ] `env.step()` 能返回符合本地版本接口的数据；
- [ ] random action 能完整运行多 episode。

---

# 7. Tutorial 3 — DirectRLEnv Reimplementation

## 7.1 教学目标

回答：

> Manager-Based 与 Direct 到底有什么区别？

使用 `DirectRLEnv` 重新实现 Tutorial 2 **完全相同的 MDP**。

## 7.2 必须保持不变

Manager 和 Direct 两版必须尽量保持：

- 相同 UAV；
- 相同 Scene；
- 相同 action definition；
- 相同 observation definition；
- 相同 fixed target；
- 相同 reward 数学形式；
- 相同 termination；
- 相同 reset distribution；
- 相同 decimation / dt；
- 相同 episode length。

## 7.3 对照关系

根据本地版本实际 API 建立文档表：

```text
Manager-Based                  Direct

SceneCfg                   ↔  _setup_scene()
ActionManager              ↔  action preprocessing/application
ObservationManager         ↔  _get_observations()
RewardManager              ↔  _get_rewards()
TerminationManager         ↔  _get_dones()
Event/reset                ↔  _reset_idx()
CommandManager             ↔  explicit target tensor/state
CurriculumManager          ↔  explicit curriculum state/update
```

不要机械使用上述函数名，如果本地 DirectRLEnv API 有变化，以实际抽象方法为准。

## 7.4 验收

- [ ] Direct env 可运行；
- [ ] Manager 和 Direct 的 observation/action shape 一致；
- [ ] 使用同一固定 initial state + action 时，短时间行为基本一致；
- [ ] reward 公式一致；
- [ ] termination 条件一致；
- [ ] 文档明确解释“同一任务的两种软件组织方式”。

---

# 8. Tutorial 4 — Gym Registration + RL Integration

## 8.1 教学目标

回答：

> 已经写好的 RL Task 如何成为 RL framework 可以训练的 environment？

本 Tutorial **不进行正式 PPO 训练**。

## 8.2 内容

必须讲清：

```text
Task ID
    ↓
Gymnasium Registry
    ↓
Env Config
    ↓
Environment instance
    ↓
RL framework wrapper
    ↓
Agent
```

## 8.3 Gym Registration

为 Manager-Based task 注册一个清晰 task id。

例如：

```text
Isaac-UAV-Hover-Manager-v0
```

如需 Direct 版：

```text
Isaac-UAV-Hover-Direct-v0
```

实际命名遵循本地项目现有 convention。

注册项应明确解释：

- `id`
- `entry_point`
- `env_cfg_entry_point`
- `skrl_cfg_entry_point`
- 其他本地版本要求的参数

## 8.4 Runtime config

展示：

```text
Config class
    ↓
gym.make(...)
    ↓
runtime env object
```

强调：

> `*Cfg` 是声明式配置，不是 runtime scene/env 本身。

## 8.5 Wrapper

检查并使用本地版本 SKRL wrapper。

典型概念：

```text
ManagerBasedRLEnv / DirectRLEnv
        ↓
SkrlVecEnvWrapper
        ↓
SKRL-compatible env
```

Wrapper 必须放在合适的 wrapper 链末端，遵守本地版本约束。

## 8.6 三种 agent 验证

在正式 PPO 前，提供：

```text
random agent
zero / sanity agent
PID baseline
```

至少 random 和 PID 应能通过同一个 registered environment 接口运行。

## 8.7 验收

- [ ] task 能被 Gymnasium 找到；
- [ ] `gym.make()` 正常；
- [ ] random action 可 step；
- [ ] PID baseline 可通过 registered env 运行；
- [ ] SKRL wrapper 正常；
- [ ] observation_space / action_space / tensor shape 输出清楚；
- [ ] 不开始正式长时间 PPO training。

---

# 9. Tutorial 5 — SKRL PPO + Goal-Conditioned Policy

## 9.1 教学目标

回答两个问题：

1. SKRL PPO 如何训练 Isaac Lab 环境？
2. 普通 fixed-goal RL 如何扩展成 goal-conditioned policy？

## 9.2 从 fixed goal 到 goal distribution

Tutorial 2：

```text
Command:
g = g0
```

Tutorial 5：

```text
Command:
g ~ p(g)
```

例如：

```text
x_goal ∈ [xmin, xmax]
y_goal ∈ [ymin, ymax]
z_goal ∈ [zmin, zmax]
```

范围初始不要过大。

## 9.3 GCRL 的关键变化：goal 进入 Observation

普通 fixed-goal：

```text
π(a | s)
```

Goal-conditioned：

```text
π(a | s, g)
```

Observation 中增加适合控制的 goal 表达，例如：

```text
goal_position - drone_position
```

必要时转换到 body frame，但必须在文档解释坐标系。

推荐 observation：

```text
proprioceptive state
+
relative goal
+
optional previous action
```

## 9.4 反例必须解释

文档明确说明：

### 情况 A

```text
Command 随机
Observation 不含 goal
```

这不是一个合理的 GC policy，因为 policy 不知道当前目标。

### 情况 B

```text
Command 固定
Observation 含 goal
```

接口形式可以写成 `π(a|s,g)`，但训练数据只有一个 goal，无法学到 goal generalization。

### 情况 C

```text
Command 随机
Observation 含 goal
```

这才是本 Tutorial 的真正 Goal-Conditioned Policy。

## 9.5 Reward

继续使用 Tutorial 2 的 reward 结构。

不要因为 GCRL 就重写完全不同的 reward。

主要变化应是：

```text
fixed g0 → sampled g
```

Reward 仍从 CommandManager 获取当前 goal。

## 9.6 Goal Curriculum

把 Tutorial 2 的简单 curriculum 升级成真正有价值的 goal curriculum：

```text
Stage 1:
    near goals

Stage 2:
    medium goal range

Stage 3:
    larger workspace
```

实现方式以本地 CurriculumManager 支持能力为准。

## 9.7 SKRL PPO

使用本地 Isaac Lab 对 SKRL 的推荐集成方式。

至少解释并实现：

- Actor；
- Critic；
- observation/action dimensions；
- policy/value network；
- PPO；
- rollout length；
- gamma；
- lambda / GAE；
- learning rate；
- minibatches；
- epochs；
- checkpoint；
- training log；
- play/evaluation。

参数初值优先参考：

1. 本地类似无人机任务；
2. 本地 Isaac Lab SKRL PPO 示例；
3. 当前项目过去已经稳定工作的参数。

不要凭空设置夸张网络或超参数。

## 9.8 Baseline comparison

至少预留统一评估接口，可比较：

```text
PID
vs
PPO Goal-Conditioned Policy
```

推荐指标：

```text
position error / RMSE
success rate
settling time
control effort
episode return
collision / failure rate
```

不要求本篇得出“RL 优于 PID”的结论。

## 9.9 验收

- [ ] sampled command 工作；
- [ ] 每个 parallel env 可有不同 goal；
- [ ] goal 进入 observation；
- [ ] policy 明确为 `π(a|s,g)`；
- [ ] reward 使用当前 sampled goal；
- [ ] PPO 可以启动训练；
- [ ] checkpoint 可保存；
- [ ] play/evaluation 可加载 checkpoint；
- [ ] 至少进行一个小规模 smoke training，确认 reward/gradient/step 流程无异常；
- [ ] 不要求 Codex 等待长时间收敛后才能继续。

---

# 10. Tutorial 6 — Replace Default UAV with Custom UAV

## 10.1 教学目标

回答：

> 如何把默认四旋翼换成自己的 UAV，而不重写整个 RL Task？

## 10.2 内容

根据用户提供或项目已有的自定义模型，优先支持：

```text
USD
或
URDF → Isaac Lab asset
```

需要检查和说明：

- root prim；
- rigid body；
- articulation（如适用）；
- collision；
- mass；
- inertia；
- center of mass；
- body frames；
- rotor/thruster frames；
- actuator / multirotor interface；
- spawn config；
- initial state。

## 10.3 最重要的设计

Task interface 尽量保持：

```text
same observation semantics
same action semantics
same command
same reward
same termination
```

只把：

```text
DefaultUAVCfg
```

替换成：

```text
CustomUAVCfg
```

如果物理模型导致 action interface 必须改变，必须在文档中明确说明为什么。

## 10.4 测试顺序

```text
spawn only
    ↓
gravity / physics sanity
    ↓
action sanity
    ↓
PID baseline
    ↓
RL environment
    ↓
PPO smoke test
```

## 10.5 验收

- [ ] 自定义模型正确生成；
- [ ] mass/inertia 等关键参数可检查；
- [ ] actuator/thrust direction 正确；
- [ ] PID 基本可控；
- [ ] ManagerBasedRLEnv 可替换资产；
- [ ] 不复制一整套新 Task 代码来实现“换机器人”。

---

# 11. Tutorial 7 — Sensors: Camera, Stereo, LiDAR

## 11.1 教学目标

回答：

> 如何给 UAV 增加外部感知，而不立刻把问题复杂化成视觉强化学习？

本篇先讲 sensor integration，不做端到端视觉 PPO。

## 11.2 Step A：单目 Camera

实现：

- camera mounting frame；
- extrinsics；
- resolution；
- update period；
- RGB；
- depth（若本地 renderer/API 支持）。

输出并检查：

```text
image shape
dtype
device
update rate
```

## 11.3 Step B：双目 Camera

增加：

```text
left camera
right camera
baseline
```

确保：

- 两相机固定在 UAV body 上；
- 相对位姿明确；
- acquisition timing 一致或尽可能同步；
- 文档解释 baseline 和 extrinsics。

此阶段只读取 left/right data，不实现完整 stereo matching，除非已有低成本本地工具。

## 11.4 Step C：LiDAR / RayCaster

优先先实现高并行 RL 友好的几何 ray sensor，例如本地 `RayCaster` 或等价接口。

如果本地版本支持 RTX LiDAR，可作为附加示例，但必须说明：

```text
RayCaster
    更适合大量并行环境中的几何距离感知

RTX / rendered sensor
    更接近真实传感器渲染，但 GPU/renderer 成本更高
```

## 11.5 性能原则

不要默认：

```text
4096 envs × stereo RGB × RTX LiDAR
```

这会让 Tutorial 失去重点。

Sensor Tutorial 默认使用较少环境，例如 1～16 个，用于功能验证。

## 11.6 验收

- [ ] 单目 camera 可读取；
- [ ] stereo pair mount 正确；
- [ ] ray/LiDAR 可感知 Tutorial 0 的柱子；
- [ ] sensor data shape/device 文档清楚；
- [ ] headless / renderer 依赖说明清楚；
- [ ] 没有在本篇同时实现复杂 CNN + PPO。

---

# 12. Tutorial 8 — Goal-Conditioned Obstacle Navigation

## 12.1 教学目标

把 Tutorial 0 的障碍环境、Tutorial 5 的 GCRL 和 Tutorial 7 的感知真正组合起来。

任务：

> UAV 从随机初始状态到达随机目标点，同时避开高低不同的柱状障碍。

## 12.2 Command

```text
goal position
g ~ valid_goal_distribution
```

必须避免把 goal 采样在：

- 柱体内部；
- 地面以下；
- environment bounds 之外；
- 明显无法到达的位置。

## 12.3 Observation

第一版优先使用低维 state + ray observation：

```text
proprioception
+
relative goal
+
LiDAR / RayCaster distances
```

即：

```text
o_t = [s_t, g_t - p_t, z_t^ray]
```

不要第一版就使用 stereo RGB CNN。

## 12.4 Action

尽量延续 Tutorial 1～5 的 action interface。

## 12.5 Reward

建议保持可解释的最小组合：

```text
goal distance / progress reward
+
goal success bonus
-
collision penalty
-
control penalty
-
optional attitude penalty
```

避免十几个 reward term 同时出现。

## 12.6 Termination

至少：

```text
goal reached
collision
out of bounds
timeout
```

## 12.7 Curriculum

推荐：

```text
Stage 1:
    no obstacles / near goal

Stage 2:
    sparse obstacles

Stage 3:
    more obstacles + larger goal range

Stage 4:
    randomized pillar height/position
```

每一步只改变少量难度变量。

## 12.8 验收

- [ ] random valid goal；
- [ ] ray sensor 能看到障碍；
- [ ] collision detection 正常；
- [ ] GC observation 正常；
- [ ] PPO smoke training 可启动；
- [ ] curriculum 可切换难度；
- [ ] 可可视化 goal 和至少部分传感结果；
- [ ] 训练接口仍与 Tutorial 5 兼容。

---

# 13. 公共代码设计要求

## 13.1 避免复制粘贴

不要让每个 Tutorial 都包含完整重复的：

- UAV asset config；
- scene config；
- reward 函数；
- PID；
- Gym registration；
- PPO config。

应把公共实现放入 package，Tutorial script 只负责演示当前概念。

## 13.2 但不要过度抽象

不要为了“零重复”创建大量只有一行代码的 helper。

原则：

> 教学可读性优先于极端 DRY。

## 13.3 Config 与 Runtime 必须在文档中区分

对所有关键对象明确：

```text
XxxCfg
    = configuration / declaration

Xxx
    = runtime object
```

尤其解释：

```text
InteractiveSceneCfg → InteractiveScene
ManagerBasedRLEnvCfg → ManagerBasedRLEnv
```

## 13.4 Tensor batch 语义

所有 Tutorial 从一开始就把并行环境作为一等概念。

文档中使用：

```text
obs.shape    = [num_envs, obs_dim]
action.shape = [num_envs, action_dim]
reward.shape ≈ [num_envs]
```

具体 shape 以本地 API 为准。

不要用“先写单环境 NumPy，最后再勉强改 batch”的方式。

## 13.5 Device

尽量保持 tensor 在 simulator / torch device 上。

避免无必要：

```text
GPU tensor → CPU numpy → GPU tensor
```

PID baseline 如必须使用 CPU 实现，则明确标记性能限制；优先实现 torch batch 版本。

---

# 14. 文档写作规则

每篇 `docs/tutorial_XX_*.md` 统一包含：

## 14.1 本篇回答的问题

只写 1 个核心问题。

## 14.2 相比上一篇新增了什么

例如：

```text
Tutorial 1 → Tutorial 2:

新增:
    CommandManager
    RewardManager
    TerminationManager
    CurriculumManager

不变:
    Scene
    UAV
    Action semantics
```

## 14.3 架构图

必须有 ASCII / Mermaid 二选一，优先 Mermaid + 纯文本 fallback。

## 14.4 核心类

只列本篇真正需要理解的 Isaac Lab 类。

## 14.5 执行链

例如 Tutorial 2：

```text
action
  ↓
ActionManager
  ↓
physics
  ↓
termination
  ↓
reward
  ↓
reset if needed
  ↓
observation
```

顺序以本地 Isaac Lab 代码为准，不能凭印象写错。

## 14.6 如何运行

给出实际可执行命令。

## 14.7 预期输出

包括：

- console；
- tensor shape；
- GUI 中应看到什么；
- 成功标准。

## 14.8 常见误解

例如：

```text
CommandManager ≠ Goal-Conditioned RL
InteractiveSceneCfg ≠ InteractiveScene
ManagerBasedRLEnv ≠ PPO
Gym task id ≠ Python class name
```

## 14.9 下一篇为什么自然出现

每一篇末尾用 2～4 句话引出下一篇。

---

# 15. GCRL 概念规范

全文统一使用以下定义。

## 15.1 Fixed-goal RL

```text
g = g0
policy observation = s
policy = π(a | s)
reward = r(s, a, g0)
```

Isaac Lab 中：

```text
CommandManager → fixed target
RewardManager  → reads target
Observation    → does not need target
```

## 15.2 Goal-Conditioned RL

```text
g ~ p(g)
policy observation = [s, g] or [s, φ(s,g)]
policy = π(a | s, g)
reward = r(s, a, g)
```

Isaac Lab 中：

```text
CommandManager
      ↓
sampled goal g
      ├────────────→ RewardManager
      │
      └────────────→ ObservationManager
                          ↓
                       policy
```

## 15.3 不允许的概念混淆

不要写：

> “添加 CommandManager 就实现了 GCRL。”

应写：

> “CommandManager 提供 goal/reference；当该 goal 被显式条件化到 policy observation，并且训练覆盖多个 goal 时，才形成真正具有 goal-conditioned 行为的 policy。”

---

# 16. PID Baseline 规范

PID 只承担以下用途：

```text
1. 验证 UAV action interface 是否合理
2. 验证 scene / physics 是否基本正确
3. 作为 RL performance baseline
```

不要：

- 用多个章节讲 PID 参数整定；
- 把 PID 设计当作本教程主线；
- 为 PID 单独设计与 RL 不兼容的 action space。

PID controller 尽量支持：

```text
batch state input
batch action output
torch tensor
```

推荐接口概念：

```python
controller = CascadedPIDController(...)
action = controller.compute(observation_or_state, target)
```

具体参数和实现可放在工具模块。

---

# 17. 测试策略

Codex 每完成一个 Tutorial，必须先运行小规模测试再进入下一篇。

## 17.1 Smoke test 优先

不要为了证明 PPO 收敛而阻塞整个工程。

建议：

```text
GUI:
    num_envs = 1 / 4

headless API test:
    num_envs = 16 / 64

PPO smoke:
    small num_envs
    small timesteps
```

只有在用户明确要求性能实验时才进行长时间训练。

## 17.2 建议自动化测试

若项目结构适合 pytest，至少覆盖：

- config can instantiate；
- env reset；
- action/observation shape；
- command shape；
- reward finite；
- no NaN；
- termination dtype/shape；
- goal differs across envs in Tutorial 5；
- custom UAV asset can spawn；
- sensor tensor shape。

不要要求 GUI test 进入普通 CI。

---

# 18. 代码质量要求

- Python 类型标注；
- 简洁 docstring；
- 避免无意义 wrapper；
- 避免巨大单文件；
- 不在函数内部到处 import，除非 Isaac Sim/Isaac Lab 的 import 顺序有硬性要求；
- 遵守 Isaac Lab `AppLauncher` / SimulationApp 的 import 时序；
- 所有需要在 App 启动后 import 的模块，必须按本地版本要求处理；
- 尽量使用 `@configclass` 和本地官方配置机制；
- 不把用户机器绝对路径写入代码；
- 不静默 catch 所有 Exception；
- 所有随机化支持 seed；
- 所有关键尺寸和坐标系有注释。

---

# 19. Codex 执行方式

按阶段执行，不要一次性生成全部代码后再测试。

推荐顺序：

```text
Phase 0
    inspect repository and local Isaac Lab
    write docs/local_environment.md

Phase 1
    implement Tutorial 0
    run smoke tests
    document

Phase 2
    implement Tutorial 1
    run PID baseline
    document

Phase 3
    implement Tutorial 2
    run random-agent RL env
    document

Phase 4
    implement Tutorial 3
    compare Direct vs Manager
    document

Phase 5
    implement Tutorial 4
    validate Gym + SKRL wrapper
    document

Phase 6
    implement Tutorial 5
    PPO smoke train + checkpoint + play
    document

Phase 7
    implement Tutorial 6
    only if a custom UAV model is available;
    otherwise create a clean adapter/config placeholder
    and document exactly what model inputs are still required

Phase 8
    implement Tutorial 7
    camera/ray sensor functional test

Phase 9
    implement Tutorial 8
    obstacle-navigation environment
    PPO smoke test
```

### 每个 Phase 完成后

记录：

```text
Files changed
Commands run
Tests passed
Known limitations
Next step
```

可写入：

```text
docs/progress.md
```

---

# 20. 遇到版本差异时的决策原则

若本文档中的类名/API 与本地 Isaac Lab 冲突：

1. 先检查本地源码和本地安装附带示例；
2. 使用本地版本实际 API；
3. 保留本文档规定的**教学语义和层级**；
4. 在对应 Tutorial 文档中注明版本差异；
5. 不为了匹配本文档而升级 Isaac Lab；
6. 不因为一个 API 不同就改变整个 Tutorial 的教学目标。

例如：

```text
“固定 Command”
```

是语义要求。

至于它通过：

```text
UniformPoseCommandCfg
自定义 CommandTerm
或本地版本其他 command config
```

实现，应由本地 API 决定。

---

# 21. 最终 README 应呈现的学习路线

README 首页应能够在 1 分钟内让读者理解：

```text
0. World
   InteractiveScene

1. Interaction
   ManagerBasedEnv
   Observation + Action + Event
   PID baseline

2. RL Task
   ManagerBasedRLEnv
   Fixed Command + Reward + Termination + Curriculum

3. Workflow
   DirectRLEnv vs Manager-Based

4. Integration
   Gym + Config + SKRL Wrapper

5. Learning
   PPO + Goal-Conditioned Policy

6. Robot
   Replace default UAV

7. Perception
   Camera + Stereo + LiDAR

8. Navigation
   Goal-conditioned obstacle avoidance
```

README 需要明确：

> 这套教程的重点是理解 Isaac Lab 强化学习的软件结构和数据流，而不是学习 PID、视觉算法或 PPO 数学推导。

---

# 22. 最终成功标准

完成后，整个项目应形成一条可连续执行的路径：

```text
InteractiveScene
    ↓
ManagerBasedEnv
    ↓
PID baseline
    ↓
ManagerBasedRLEnv
    ↓
DirectRLEnv comparison
    ↓
Gym registration
    ↓
SKRL wrapper
    ↓
PPO fixed/GC task
    ↓
custom UAV
    ↓
onboard sensors
    ↓
obstacle navigation
```

并满足：

- [ ] 每个 Tutorial 独立可运行；
- [ ] 每篇建立在上一篇之上；
- [ ] 无不必要的机器人/任务切换；
- [ ] PID 与 RL 环境解耦；
- [ ] CommandManager 与 GCRL 概念不混淆；
- [ ] Tutorial 2 明确是 fixed-goal RL；
- [ ] Tutorial 5 明确展示 `π(a|s) → π(a|s,g)`；
- [ ] Manager 和 Direct 实现同一 MDP；
- [ ] Gym / Config / Wrapper 有独立 Tutorial；
- [ ] 默认 UAV 可替换；
- [ ] Sensor 集成和视觉 RL 解耦；
- [ ] Tutorial 0 的柱状障碍最终在 Tutorial 8 被真正利用；
- [ ] 所有代码优先兼容用户本地 Isaac Lab 版本；
- [ ] 所有 Tutorial 都提供运行命令和验收标准。

---

# 23. Codex 开始执行时的第一条指令

在开始修改前：

> 先阅读整个本文档、当前仓库中的 `AGENTS.md`（如存在）、项目 README 和现有代码；检查本地 Isaac Lab/Isaac Sim/SKRL 版本与 API；先输出并写入 `docs/local_environment.md`，然后从 Tutorial 0 开始逐阶段实施和测试。不要跳过前置检查，不要一次性生成全部 Tutorial，不要为了适配网上最新文档而升级本地环境。
