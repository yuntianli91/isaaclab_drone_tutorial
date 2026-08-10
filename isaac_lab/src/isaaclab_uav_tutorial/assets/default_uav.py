"""整个 Tutorial 系列使用的默认 UAV 资产。"""

from isaaclab.assets import ArticulationCfg
from isaaclab_assets import CRAZYFLIE_CFG

# 先复制内置 Crazyflie 配置，保留 USD、刚体属性、执行器和旋翼关节初始状态。
DEFAULT_UAV_CFG: ArticulationCfg = CRAZYFLIE_CFG.copy()

# 在项目内显式覆盖 root 初始状态，修改下列元组即可手工调整起始状态。
DEFAULT_UAV_CFG.init_state.pos = (0.0, 0.0, 0.1)      # 初始位置 (m)。
DEFAULT_UAV_CFG.init_state.lin_vel = (0.0, 0.0, 0.0)  # 初始线速度 (m/s)。
DEFAULT_UAV_CFG.init_state.ang_vel = (0.0, 0.0, 0.0)  # 初始角速度 (rad/s)。
