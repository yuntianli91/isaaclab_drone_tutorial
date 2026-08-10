"""供后续导航 Tutorial 复用的 UAV 与静态柱体场景。"""

from __future__ import annotations

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass

from isaaclab_uav_tutorial.assets import DEFAULT_UAV_CFG


# ===== _pillar_cfg ========================================================== #
def _pillar_cfg(prim_name: str,
                position: tuple[float, float, float],
                size: tuple[float, float, float],
                color: tuple[float, float, float]) -> AssetBaseCfg:
  """创建一个会复制到每个环境中的静态可碰撞柱体。

  Args:
    prim_name: 柱体在环境命名空间中的 Prim 名称。
    position: 柱体中心相对环境原点的位置 (m)。
    size: 柱体沿 X、Y、Z 轴的尺寸 (m)。
    color: RGB 漫反射颜色。

  Returns:
    可供 :class:`InteractiveSceneCfg` 使用的静态资产配置。
  """
  return AssetBaseCfg(
    prim_path=f"{{ENV_REGEX_NS}}/{prim_name}",   # 每个环境内的 Prim 路径。
    spawn=sim_utils.CuboidCfg(                   # 柱体生成配置。
      size=size,                                 # 柱体尺寸 (m)。
      collision_props=sim_utils.CollisionPropertiesCfg(
        collision_enabled=True                   # 启用碰撞。
      ),                                         # 碰撞属性。
      rigid_props=sim_utils.RigidBodyPropertiesCfg(
        kinematic_enabled=True                   # 固定为运动学刚体。
      ),                                         # 刚体属性。
      visual_material=sim_utils.PreviewSurfaceCfg(
        diffuse_color=color, roughness=0.8       # 颜色和粗糙度。
      ),                                         # 可视材质。
    ),                                           # 柱体几何。
    init_state=AssetBaseCfg.InitialStateCfg(
      pos=position                               # 初始位置 (m)。
    ),                                           # 初始状态。
  )


@configclass
class UavObstacleSceneCfg(InteractiveSceneCfg):
  """声明默认 UAV、地面、灯光和三根静态柱体。"""

  ground = AssetBaseCfg(
    prim_path="/World/defaultGroundPlane",   # 全局地面 Prim 路径。
    spawn=sim_utils.GroundPlaneCfg(),        # 生成无限平面。
    collision_group=-1,                      # 与所有环境发生碰撞。
  )                                          # 公共地面资产。

  dome_light = AssetBaseCfg(
    prim_path="/World/Light",                # 全局灯光 Prim 路径。
    spawn=sim_utils.DomeLightCfg(
      intensity=2500.0, color=(0.75, 0.75, 0.75)  # 强度和 RGB 颜色。
    ),                                          # 灯光生成配置。
  )                                          # 公共穹顶灯光。

  uav: ArticulationCfg = DEFAULT_UAV_CFG.replace(
    prim_path="{ENV_REGEX_NS}/UAV"           # 每个环境中的 UAV Prim。
  )                                          # 默认 Crazyflie 资产。

  pillar_tall = _pillar_cfg(
    prim_name="PillarTall",                  # 高柱体 Prim 名称。
    position=(1.5, 1.0, 1.25),               # 中心位置 (m)。
    size=(0.45, 0.45, 2.5),                  # 几何尺寸 (m)。
    color=(0.65, 0.22, 0.18),                # RGB 颜色。
  )                                          # 高柱体资产。
  pillar_medium = _pillar_cfg(
    prim_name="PillarMedium",                # 中柱体 Prim 名称。
    position=(-1.5, 0.8, 0.8),               # 中心位置 (m)。
    size=(0.6, 0.6, 1.6),                    # 几何尺寸 (m)。
    color=(0.18, 0.42, 0.65),                # RGB 颜色。
  )                                          # 中柱体资产。
  pillar_low = _pillar_cfg(
    prim_name="PillarLow",                   # 低柱体 Prim 名称。
    position=(0.3, -1.6, 0.5),               # 中心位置 (m)。
    size=(0.8, 0.8, 1.0),                    # 几何尺寸 (m)。
    color=(0.28, 0.58, 0.30),                # RGB 颜色。
  )                                          # 低柱体资产。
