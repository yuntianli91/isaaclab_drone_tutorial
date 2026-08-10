"""Tutorial 1 使用的 ManagerBasedEnv 配置。

这个文件把 Tutorial 0 的公共场景包装成具有观测、动作和重置接口的
环境。
它只涉及以下三个 Manager：

* :class:`ObservationManager`：从仿真状态中组织批量观测；
* :class:`ActionManager`：把归一化动作转换为无人机受到的推力和力矩；
* :class:`EventManager`：在环境 reset 时随机化无人机初始状态。

固定悬停目标和 PID 控制器不属于环境，因此没有放在本文件中。PID
作为外部 Agent 读取 ``observation["policy"]``，并产生与后续 RL
policy 相同语义的动作。本阶段也刻意不包含
CommandManager、RewardManager、TerminationManager 或 Gym 注册。
"""

from __future__ import annotations

import isaaclab.envs.mdp as mdp
from isaaclab.envs import ManagerBasedEnvCfg
from isaaclab.managers import EventTermCfg as EventTerm
from isaaclab.managers import ObservationGroupCfg as ObsGroup
from isaaclab.managers import ObservationTermCfg as ObsTerm
from isaaclab.managers import SceneEntityCfg
from isaaclab.utils import configclass

from isaaclab_uav_tutorial.actions import UavBodyWrenchActionCfg
from isaaclab_uav_tutorial.scenes import UavObstacleSceneCfg


@configclass
class ActionsCfg:
  """声明 ActionManager 中启用的全部动作项。

  当前只有一个 ``body_wrench`` term，所以 ActionManager 的最终动作
  仍为四维。这里的
  ``asset_name="uav"`` 对应 :class:`UavObstacleSceneCfg` 中的 ``uav`` 字段。
  """

  body_wrench = UavBodyWrenchActionCfg(  # UAV wrench 动作项。
    asset_name="uav"                     # 场景资产键。
  )


@configclass
class ObservationsCfg:
  """声明 ObservationManager 输出的纯状态观测。

  Tutorial 1 的目标由外部 PID 参数提供，因此这里不把悬停目标拼入
  观测。Tutorial 2 引入
  CommandManager 后才会明确区分 state 和 command，并决定 policy 是否能观察目标。
  """

  @configclass
  class PolicyCfg(ObsGroup):
    """供外部控制器或未来 policy 使用的 ``policy`` 观测组。

    属性声明顺序就是 ``concatenate_terms=True`` 时的 tensor 拼接顺序：

    ``local_position(3), orientation_wxyz(4),``
    ``linear_velocity_w(3), angular_velocity_b(3)``

    因此 ``observation["policy"]`` 的形状为 ``(num_envs, 13)``。
    """

    local_position = ObsTerm(                         # 局部位置项。
      func=mdp.root_pos_w,                            # 官方局部位置项。
      params={"asset_cfg": SceneEntityCfg("uav")},    # UAV 场景实体。
    )
    orientation_wxyz = ObsTerm(                       # 姿态四元数项。
      func=mdp.root_quat_w,                           # 官方根姿态项。
      params={                                        # 观测项参数。
        "make_quat_unique": False,                   # 保留原始 WXYZ 表示。
        "asset_cfg": SceneEntityCfg("uav"),          # UAV 场景实体。
      },
    )
    linear_velocity_w = ObsTerm(                      # world 线速度项。
      func=mdp.root_lin_vel_w,                        # 官方 world 线速度项。
      params={"asset_cfg": SceneEntityCfg("uav")},    # UAV 场景实体。
    )
    angular_velocity_b = ObsTerm(                     # body 角速度项。
      func=mdp.base_ang_vel,                          # 官方 body 角速度项。
      params={"asset_cfg": SceneEntityCfg("uav")},    # UAV 场景实体。
    )

    # ===== __post_init__ ==================================================== #
    def __post_init__(self) -> None:
      """关闭观测噪声，并将四个 ObsTerm 自动拼接成单个 tensor。"""
      self.enable_corruption = False   # 不引入观测噪声。
      self.concatenate_terms = True    # 拼接成 (N, 13) tensor。

  policy: PolicyCfg = PolicyCfg()  # 提供给外部 Agent 的观测组。


@configclass
class EventsCfg:
  """声明 reset 阶段执行的轻量随机化事件。

  ``reset_root_state_uniform`` 先读取 Crazyflie 的默认 root state，
  再叠加采样的位姿和速度扰动。位置最终还会加上每个 clone 的
  ``env_origin``，所以执行 reset 时不会错误地把所有无人机都写回
  world 原点。

  本阶段只使用小扰动验证初始状态随机化，不在这里展开质量、摩擦或外力等 domain
  randomization。
  """

  reset_uav = EventTerm(                   # UAV reset 事件。
    func=mdp.reset_root_state_uniform,     # 均匀随机 root state。
    mode="reset",                          # 只在 env.reset(...) 时触发。
    params={                               # reset 函数参数。
      "pose_range": {                      # 相对默认位姿的扰动。
        "x": (-0.10, 0.10),                # X 位置范围 (m)。
        "y": (-0.10, 0.10),                # Y 位置范围 (m)。
        "z": (-0.05, 0.05),                # Z 位置范围 (m)。
        "roll": (-0.05, 0.05),             # roll 范围 (rad)。
        "pitch": (-0.05, 0.05),            # pitch 范围 (rad)。
        "yaw": (-0.10, 0.10),              # yaw 范围 (rad)。
      },
      "velocity_range": {                  # 线速度与角速度扰动。
        "x": (-0.05, 0.05),                # X 线速度范围 (m/s)。
        "y": (-0.05, 0.05),                # Y 线速度范围 (m/s)。
        "z": (-0.05, 0.05),                # Z 线速度范围 (m/s)。
        "roll": (-0.05, 0.05),             # roll 角速度范围 (rad/s)。
        "pitch": (-0.05, 0.05),            # pitch 角速度范围 (rad/s)。
        "yaw": (-0.05, 0.05),              # yaw 角速度范围 (rad/s)。
      },
      "asset_cfg": SceneEntityCfg("uav"),  # UAV 场景实体。
    },
  )


@configclass
class HoverManagerEnvCfg(ManagerBasedEnvCfg):
  """组合 Tutorial 1 完整非 RL 环境的顶层配置。

  :class:`ManagerBasedEnv` 会依次创建公共 Scene、EventManager、
  ActionManager 和 ObservationManager。运行入口可以在实例化环境前覆盖
  ``scene.num_envs``、
  ``scene.env_spacing``、``sim.device`` 和 ``seed``，因此这里的数量只是默认值。
  """

  scene: UavObstacleSceneCfg = UavObstacleSceneCfg(
    num_envs=1, env_spacing=6.0, replicate_physics=True  # 公共场景参数。
  )                                                     # Tutorial 0 场景。
  observations: ObservationsCfg = ObservationsCfg()     # 观测 Manager 配置。
  actions: ActionsCfg = ActionsCfg()                    # 动作 Manager 配置。
  events: EventsCfg = EventsCfg()                       # 事件 Manager 配置。

  # ===== __post_init__ ====================================================== #
  def __post_init__(self) -> None:
    """设置仿真频率、默认随机种子以及 viewer 参数。"""
    self.sim.dt = 0.01                          # 物理周期 (s)。
    self.decimation = 2                         # 控制周期为 2 个物理周期。
    self.sim.render_interval = self.decimation  # 渲染周期同样为2个物理周期。
    self.seed = 42                              # reset 随机种子。
    self.wait_for_textures = False              # 不等待 RTX 纹理。
    self.ui_window_class_type = None            # 不创建 Manager 调试 UI。
    self.viewer.eye = (9.0, 9.0, 7.0)           # 相机位置 (m)。
    self.viewer.lookat = (0.0, 0.0, 0.8)        # 相机注视点 (m)。
