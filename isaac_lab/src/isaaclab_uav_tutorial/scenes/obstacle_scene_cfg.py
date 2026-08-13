"""供后续导航 Tutorial 复用的 UAV 与静态柱体场景。"""

from __future__ import annotations

import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg, AssetBaseCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.utils import configclass

from isaaclab_uav_tutorial.assets import DEFAULT_UAV_CFG

_DOME_LIGHT_CFG = sim_utils.DomeLightCfg(intensity=2500.0,          # 渲染强度。
                                         color=(0.75, 0.75, 0.75))  # RGB 颜色。


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
  collision_cfg = sim_utils.CollisionPropertiesCfg(collision_enabled=True)
  rigid_cfg = sim_utils.RigidBodyPropertiesCfg(kinematic_enabled=True)
  material_cfg = sim_utils.PreviewSurfaceCfg(diffuse_color=color,
                                              roughness=0.8)
  spawn_cfg = sim_utils.CuboidCfg(size=size,
                                  collision_props=collision_cfg,
                                  rigid_props=rigid_cfg,
                                  visual_material=material_cfg)
  initial_state_cfg = AssetBaseCfg.InitialStateCfg(pos=position)
  return AssetBaseCfg(prim_path=f"{{ENV_REGEX_NS}}/{prim_name}",
                      spawn=spawn_cfg, init_state=initial_state_cfg)


@configclass
class UavObstacleSceneCfg(InteractiveSceneCfg):
  """声明默认 UAV、地面、灯光和三根静态柱体。"""

  ground = AssetBaseCfg(prim_path="/World/defaultGroundPlane",   # 地面 Prim。
                        spawn=sim_utils.GroundPlaneCfg(),        # 地面配置。
                        collision_group=-1)                      # 全局碰撞组。

  dome_light = AssetBaseCfg(prim_path="/World/Light",   # 灯光 Prim。
                            spawn=_DOME_LIGHT_CFG)      # 灯光配置。

  # 默认 Crazyflie 资产。
  uav: ArticulationCfg = DEFAULT_UAV_CFG.replace(prim_path="{ENV_REGEX_NS}/UAV")

  pillar_tall = _pillar_cfg(prim_name="PillarTall",     # 高柱体 Prim。
                            position=(1.5, 1.0, 1.25),  # 中心位置 (m)。
                            size=(0.45, 0.45, 2.5),     # 几何尺寸 (m)。
                            color=(0.65, 0.22, 0.18))   # RGB 颜色。
  pillar_medium = _pillar_cfg(prim_name="PillarMedium",   # 中柱体 Prim。
                              position=(-1.5, 0.8, 0.8),  # 中心位置 (m)。
                              size=(0.6, 0.6, 1.6),       # 几何尺寸 (m)。
                              color=(0.18, 0.42, 0.65))   # RGB 颜色。
  pillar_low = _pillar_cfg(prim_name="PillarLow",       # 低柱体 Prim。
                           position=(0.3, -1.6, 0.5),   # 中心位置 (m)。
                           size=(0.8, 0.8, 1.0),        # 几何尺寸 (m)。
                           color=(0.28, 0.58, 0.30))    # RGB 颜色。
