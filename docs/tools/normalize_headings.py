"""Normalize and number headings in generated tutorial HTML pages."""

from pathlib import Path
from urllib.parse import urljoin

from lxml import etree, html


DOCUMENT_ROOT = Path(
  "/home/yuntian/gitRepos/isaac_tutorial/docs/isaaclab-v2.3.2-zh"
)
OFFICIAL_HTML_ROOT = Path("/tmp/isaaclab-v2.3.2-html")
OFFICIAL_BASE_URL = "https://isaac-sim.github.io/IsaacLab/v2.3.2/"
APP_LAUNCHER_LINK = (
  "https://isaac-sim.github.io/IsaacLab/v2.3.2/source/api/lab/"
  "isaaclab.app.html#isaaclab.app.AppLauncher"
)
SIMULATION_APP_LINK = (
  "https://docs.isaacsim.omniverse.nvidia.com/6.0.1/py/source/"
  "extensions/isaacsim.simulation_app/docs/index.html#"
  "isaacsim.simulation_app.SimulationApp"
)


# ===== Build an inline API link ============================================= #
def _api_link(url, label):
  return (
    f'<a class="reference external" href="{url}">'
    f'<code class="docutils literal notranslate">{label}</code></a>'
  )


# ===== Replace one paragraph ================================================ #
def _replace_paragraph(paragraph, markup):
  replacement = html.fragment_fromstring(f"<p>{markup}</p>")
  paragraph.getparent().replace(paragraph, replacement)


# ===== Build reviewed tutorial introductions ================================ #
def _reviewed_introductions():
  term = lambda value: f'<span class="term">{value}</span>'
  code = lambda value: f'<code>{value}</code>'
  return {
    "spawn_prims.html": (
      "本教程介绍如何通过 Python 在 Isaac Lab 的 "
      f"{term('Scene')} 中生成不同的 {term('Object')}（或 "
      f"{term('Prim')}）。内容承接上一节的独立脚本启动流程，并演示如何"
      f"生成 {term('Ground Plane')}、{term('Light')}、基本几何体，以及"
      f"如何从 USD 文件加载 Mesh。",
    ),
    "add_new_robot.html": (
      f"在 Isaac Lab 中仿真和训练新的 {term('Robot')} 通常包括多个步骤。"
      "首先需要将 Robot 导入 Isaac Sim，并根据仿真需求检查模型。之后还需"
      "定义统一接口，以便复制多个 Robot、驱动关节，并在不同 Workflow 或"
      "训练 Framework 中正确执行 Reset。",
      f"本教程说明如何向 Isaac Lab 添加新的 {term('Robot')}。关键工作是"
      f"创建 {code('AssetBaseCfg')}，用它连接 USD 中的 Articulation 与 "
      "Isaac Lab 提供的控制及学习接口。",
    ),
    "run_articulation.html": (
      f"本教程介绍如何与仿真中的 {term('Articulation')} Robot 交互。"
      "在上一节 Rigid Object 操作的基础上，我们将进一步学习设置关节状态，"
      "并向 Robot 的关节发送 Command。",
    ),
    "run_deformable_object.html": (
      f"{term('Deformable Object')} 可以泛指布料、流体和 Soft Body；"
      "在 PhysX 的术语中，本教程讨论的 Deformable Object 特指 Soft Body。"
      "与 Rigid Object 不同，Soft Body 会在外力和 Collision 作用下发生形变。",
      "PhysX 使用有限元方法（FEM）模拟 Soft Body。一个 Soft Body 包含"
      "用于计算形变的 Simulation Mesh，以及用于检测碰撞的 Collision Mesh。"
      "有关实现细节，请参阅 PhysX 文档。",
      f"本教程将在 {term('Scene')} 中生成多个软立方体，演示如何设置其"
      "节点位置和速度，以及如何向 Mesh 节点施加运动学 Command 来控制形变。",
    ),
    "run_rigid_object.html": (
      f"前面的教程介绍了 {term('Standalone Script')} 的基本结构，以及如何"
      f"在仿真中生成 Object（或 Prim）。本教程将使用 Isaac Lab 的 "
      f"{code('assets.RigidObject')} Class，创建 Rigid Object 并与之交互。",
    ),
    "run_surface_gripper.html": (
      f"本教程介绍如何操作末端执行器装有 {term('Surface Gripper')} 的 "
      "Articulation Robot。内容建立在上一节 Articulation 操作的基础上。"
      "请注意，从 Isaac Sim 5.0 开始，Surface Gripper Backend 仅支持 CPU。",
    ),
    "create_scene.html": (
      f"此前的教程需要手动向 {term('Scene')} 中生成 Asset，并逐个创建用于"
      f"交互的 Object 实例。随着 Scene 变得复杂，这种方式会越来越繁琐。"
      f"本教程将介绍 {code('scene.InteractiveScene')}，使用统一接口生成 "
      "Prim 并管理仿真中的实体。",
      f"从较高层次看，{term('Interactive Scene')} 是一组 Scene 实体的集合。"
      "实体既可以是 Ground Plane、Light 等非交互式 Prim，也可以是 "
      "Articulation、Rigid Object 等交互式 Prim，还可以是 Camera、LiDAR "
      "等 Sensor。",
      "与手动管理方式相比，Interactive Scene 具有以下优点：",
      "本教程将改造上一节的 Cartpole 示例，用 InteractiveScene 取代"
      "手写的场景创建函数。虽然该示例规模较小，但随着 Asset 和 Sensor 数量"
      "增加，统一的 Scene 管理接口会显著降低代码复杂度。",
    ),
    "configuring_rl_training.html": (
      "上一节使用 Stable-Baselines3 训练 RL Agent，完成了 Cartpole 平衡"
      "任务。本教程将进一步说明如何选择不同的 RL Library 和算法，并配置"
      "相应的训练参数。",
      f"{code('scripts/reinforcement_learning')} 目录按 RL Library 名称"
      "划分子目录，每个子目录都包含该 Library 对应的训练和推理脚本。",
      f"要让某个 RL Library 用于特定 {term('Task')}，需要先创建 Agent "
      "Configuration，再像注册 Environment 一样，通过 "
      f"{code('gymnasium.register()')} 注册配置入口。训练脚本随后会读取该"
      "配置并创建 Agent。",
    ),
    "create_direct_rl_env.html": (
      f"{code('envs.ManagerBasedRLEnv')} 通过 Configuration Class 和 "
      f"Manager 构建模块化 Environment；{code('DirectRLEnv')} 则允许用户"
      "直接在 Environment Class 中实现核心逻辑，从而获得更细粒度的控制。",
      f"{term('Direct Workflow')} 不使用 Manager 定义 Reward 和 "
      "Observation，而是在 Task 脚本中直接实现相关函数。这种方式更便于使用"
      " PyTorch JIT 等功能，也让各项计算逻辑集中在同一个 Class 中。",
      f"本教程将通过 {term('Direct Workflow')} 实现 Cartpole 平衡任务，"
      "依次介绍 Scene 创建、Action 应用、Reset、Reward 和 Observation 的"
      "实现方法。",
    ),
    "create_manager_base_env.html": (
      f"{term('Environment')} 将 Scene、Observation Space、Action Space 和 "
      "Reset Event 等仿真要素组合为统一接口。在 Isaac Lab 中，Manager-Based "
      f"Environment 主要由 {code('envs.ManagerBasedEnv')} 和 "
      f"{code('envs.ManagerBasedRLEnv')} 实现。后者增加了 Reward、"
      "Termination、Curriculum 和 Command，适用于 RL Task；前者更适合传统"
      "Robot 控制。",
      f"本教程以 Cartpole 为例，介绍 {code('envs.ManagerBasedEnv')} 及其 "
      f"Configuration Class {code('envs.ManagerBasedEnvCfg')}，并说明 "
      "Manager-Based Workflow 的各个组成部分。",
    ),
    "create_manager_rl_env.html": (
      "上一节创建了 Manager-Based Base Environment，本教程将在此基础上"
      "加入 Task 定义，构建用于 Reinforcement Learning 的 Manager-Based "
      "RL Environment。",
      f"基础 {term('Environment')} 提供感知—行动接口：Agent 向 Environment "
      "发送 Action，并接收 Observation。导航、平衡等学习任务还需要明确目标，"
      f"因此 {code('envs.ManagerBasedRLEnv')} 在基础接口上增加了 Task 相关"
      "机制。",
      f"Isaac Lab 推荐通过 {code('envs.ManagerBasedRLEnvCfg')} 配置 Task，"
      "而不是直接修改 Environment Base Class。这样可以分离 Task 规范和"
      "Environment 实现，并复用相同的组件。",
      "本教程将配置 Cartpole 平衡任务，介绍如何通过 Reward Term、"
      "Termination、Curriculum 和 Command 完整描述学习目标。",
    ),
    "modify_direct_rl_env.html": (
      "前面的教程介绍了如何创建 Direct Workflow RL Environment、注册 Task，"
      "以及训练 RL Agent。本教程将在这些内容的基础上，修改一个现有 Task。",
      "当目标与已有示例差异较大时，可能需要从头实现 Task；如果差异较小，"
      "则可以复制现有实现并只修改必要部分，从而减少重复工作。",
      "本教程将修改 Direct Workflow Humanoid Task，把原有 Humanoid 模型"
      "替换为 Unitree H1 Robot，同时保持原始 Task 逻辑不变。",
    ),
    "policy_inference_in_usd.html": (
      "上一节介绍了如何修改现有 Direct RL Environment。本教程将进一步说明"
      "如何在预先构建的 USD Scene 中运行已经训练好的 Policy。",
      "示例使用 RSL-RL 为 Isaac-Velocity-Rough-H1-v0 Task 训练的 H1 Rough "
      "Terrain Policy，并在一个简化的仓库 USD Scene 中执行推理。",
    ),
    "register_rl_env_gym.html": (
      "上一节创建 Cartpole Environment 时，需要直接导入 Environment Class "
      "及其 Configuration Class，然后手动创建实例。",
      f"这种方式适合单个示例，但难以管理大量 {term('Environment')}。本教程"
      f"将使用 {code('gymnasium.register()')} 注册 Environment，使其能够通过 "
      f"{code('gymnasium.make()')} 按名称创建。",
    ),
    "run_rl_training.html": (
      "前面的教程已经完成 RL Task Environment 的定义与注册，并使用 Random "
      "Agent 验证了交互流程。接下来将进入训练阶段，让 RL Agent 学习解决该 Task。",
      f"虽然 {code('envs.ManagerBasedRLEnv')} 遵循 "
      f"{code('gymnasium.Env')} 接口，但它面向并行仿真：输入和输出使用 Torch "
      "Tensor，并以第一维表示 Environment 数量，而不是传统的 NumPy Array。",
      "不同 RL Library 对 Environment Interface 的要求并不相同。例如，"
      "Stable-Baselines3、RSL-RL、RL-Games 和 SKRL 分别使用不同的数据格式。"
      "Isaac Lab 因此在 isaaclab_rl Module 中提供对应 Wrapper，将统一的"
      " Environment 转换为各 Library 所需的接口。",
      "本教程将使用 Stable-Baselines3 训练 RL Agent，解决 Cartpole 平衡任务。",
    ),
    "add_sensors_on_robot.html": (
      f"Asset Class 用于创建和模拟 {term('Robot')} 的物理实体，Sensor 则用于"
      "感知 Environment。Sensor 的更新频率通常低于 Simulation，可提供"
      "本体感知或外部感知信息。例如，Camera 获取视觉数据，Contact Sensor "
      "检测 Robot 与 Environment 的接触状态。",
      "本教程以具有12个自由度的 ANYmal-C 四足 Robot 为例，演示如何添加"
      "不同类型的 Sensor。ANYmal-C 的四条腿各包含3个自由度。",
      f"本教程延续上一节的 {term('Interactive Scene')} 示例，并在 "
      f"{code('scene.InteractiveScene')} 中配置和管理这些 Sensor。",
    ),
    "run_diff_ik.html": (
      "前面的教程主要在 Joint Space 中控制 Robot。在许多应用中，直接指定"
      "末端执行器的目标 Pose 更直观，例如遥操作场景；此时可以使用 "
      "Task-Space Controller，而不必逐个给出关节目标位置。",
      f"本教程使用 {code('controllers.DifferentialIKController')} 跟踪"
      "末端执行器的目标 Pose，介绍 Differential IK Controller 的基本用法。",
    ),
    "run_osc.html": (
      "Differential IK Controller 主要用于控制末端执行器 Pose，但某些任务"
      "还需要指定误差动态、直接发送关节力矩，或在控制运动的同时沿特定方向"
      "施加接触力。此类任务可以使用 Operational Space Controller（OSC）。",
      "有关 Operational Space Control 的理论背景，请参阅下列资料：",
      f"本教程使用 {code('controllers.OperationalSpaceController')} 控制 "
      "Robot：在垂直于倾斜墙面的方向施加恒定力，同时在其他方向跟踪目标"
      "末端执行器 Pose。",
    ),
  }


# ===== Apply reviewed tutorial introductions ================================ #
def _apply_reviewed_introductions(tree, page_path):
  introductions = _reviewed_introductions().get(page_path.name)
  if not introductions:
    return
  articles = tree.xpath("//article")
  if not articles:
    return
  sections = articles[0].xpath("./section")
  container = sections[0] if sections else articles[0]
  paragraphs = container.xpath("./p")
  for paragraph, introduction in zip(paragraphs, introductions):
    _replace_paragraph(paragraph, introduction)


# ===== Correct recurring machine-translation errors ======================== #
def _apply_recurring_prose_fixes(tree):
  replacements = (
    ("这个Script", "该 Script"),
    ("这个Class", "该 Class"),
    ("这个Method", "该 Method"),
    ("这个Noise", "该 Noise"),
    ("这 ", "该 "),
    ("产卵", "生成"),
    ("健身房注册表", "Gymnasium Registry"),
    ("传统的健身房", "传统 Gymnasium"),
    ("密钥", "键"),
    ("打训练好的", "运行训练好的"),
    ("申请Actions", "应用 Actions"),
    ("申请 Actions", "应用 Actions"),
    ("计算完成并执行Reset", "计算终止状态并执行 Reset"),
    ("定义在中的", "定义在"),
    ("被摄入", "传递给"),
    ("稳定基线3", "Stable-Baselines3"),
    ("RL-游戏", "RL-Games"),
    ("推杆平衡", "Cartpole 平衡"),
    ("底座 Environment", "基础 Environment"),
    ("直接 Environments", "Direct Environments"),
    ("高度扫描仪", "Height Scanner"),
    ("互动执行", "交互式执行"),
    ("获取Robot", "获取 Robot"),
    ("运行Simulation", "运行 Simulation"),
    ("从Python", "从 Python"),
    ("Python将", "Python 将"),
    ("对于 例如", "例如"),
    ("为了做到这一点", "为了简化这一过程"),
    ("新Class", "新 Class"),
    ("的Class", "的 Class"),
    ("使用Configuration", "使用 Configuration"),
    ("图书馆", "Library"),
    ("包裹", "Package"),
    ("财产", "Property"),
    ("批量返回 时尚", "以批量形式返回"),
    ("一刀切的方法 解决方案", "适用于所有情况的统一方案"),
    ("联合 Positions", "关节 Position"),
    ("联合 Velocities", "关节 Velocity"),
    ("远光", "Distant Light"),
    ("车杆", "Cartpole"),
    ("推杆", "Cartpole"),
    ("手推车", "滑车"),
    ("身体指数", "刚体索引"),
    ("个人 Environments", "各个 Environment"),
    ("个人 Terms", "各个 Term"),
    ("引擎盖下", "内部"),
    ("Command 一代", "Command 生成"),
    ("被按死", "按下"),
    ("接头", "关节"),
    ("指向其他 Prims 的指针", "指向其他 Prims 的 pointer"),
  )
  nodes = tree.xpath(
    "//text()[not(ancestor::pre) and not(ancestor::code) "
    "and not(ancestor::script) and not(ancestor::style)]"
  )
  for node in nodes:
    updated = str(node)
    for source, target in replacements:
      updated = updated.replace(source, target)
    if updated == str(node):
      continue
    parent = node.getparent()
    if node.is_text:
      parent.text = updated
    else:
      parent.tail = updated


# ===== Correct source-location sentences ==================================== #
def _correct_source_location_paragraphs(tree):
  for paragraph in tree.xpath("//article//p"):
    text = " ".join(paragraph.text_content().split())
    if "该教程对应的是" not in text:
      continue
    code_values = [
      "".join(code_element.itertext()).strip()
      for code_element in paragraph.xpath(".//code")
    ]
    if len(code_values) < 2:
      continue
    script_name = code_values[0]
    directory = code_values[1]
    replacement = (
      f"本教程对应 <code>{script_name}</code>，位于 "
      f"<code>{directory}</code> 目录。"
    )
    _replace_paragraph(paragraph, replacement)


# ===== Correct isolated malformed paragraphs =============================== #
def _correct_isolated_paragraphs(tree, page_path):
  if page_path.name != "spawn_prims.html":
    return
  for paragraph in tree.xpath("//article//p"):
    value = " ".join(paragraph.text_content().split())
    if not value.startswith("Relationships："):
      continue
    _replace_paragraph(
      paragraph,
      "Relationships：表示 Prim 之间的连接，可以理解为指向其他 Prim 的 "
      "<code>pointer</code>。例如，Mesh Prim 可以通过 Relationship 关联 "
      "Material Prim，以指定着色材质。",
    )


# ===== Correct reviewed heading translations ================================ #
def _apply_heading_corrections(tree):
  corrections = {
    "the-code-explained": "代码解析",
    "adding-arguments-to-the-argparser": "向 ArgumentParser 添加参数",
    "understanding-the-output-of-help": "理解 --help 的输出",
    "using-environment-variables": "使用环境变量",
    "spawning-a-ground-plane": "生成 Ground Plane",
    "spawning-lights": "生成 Light",
    "spawning-primitive-shapes": "生成 Primitive Shapes",
    "spawning-from-another-file": "从文件加载 Asset",
    "executing-the-script": "执行 Script",
    "resetting-the-simulation-state": "重置 Simulation 状态",
    "resetting-the-simulation": "重置 Simulation",
    "scene-creation": "创建 Scene",
    "computing-dones-and-performing-resets": "计算终止状态并执行 Reset",
    "applying-actions": "应用 Actions",
    "running-the-simulation": "运行 Simulation",
    "using-the-gym-registry": "使用 Gymnasium Registry",
    "direct-environments": "Direct Environments",
    "headless-execution": "Headless 模式",
    "headless-execution-with-off-screen-render": (
      "Headless 模式与 Off-Screen Rendering"
    ),
    "playing-the-trained-agent": "运行训练好的 Agent",
    "the-changes-explained": "修改说明",
    "obtaining-the-robot-s-joint-and-body-indices": (
      "获取 Robot 的关节与刚体索引"
    ),
  }
  for heading_id, label in corrections.items():
    headings = tree.xpath(
      "//h2[@id=$heading_id] | //h3[@id=$heading_id] | "
      "//h4[@id=$heading_id]",
      heading_id=heading_id,
    )
    for heading in headings:
      replacement = etree.Element(heading.tag)
      replacement.attrib.update(heading.attrib)
      replacement.text = label
      heading.getparent().replace(heading, replacement)


# ===== Build reviewed section prose ========================================= #
def _reviewed_section_prose():
  return {
    "adding-arguments-to-the-argparser": (
      "AppLauncher 可以与脚本自定义的 CLI 参数共同使用，同时提供统一、可移植"
      "的启动接口。",
      "本教程创建一个 argparse.ArgumentParser，并添加脚本专用参数 --size，"
      "以及将传递给 SimulationApp 的 --height 和 --width。",
      "--size 不由 AppLauncher 处理，但可以与 AppLauncher 参数合并到同一个 "
      "ArgumentParser 中。调用 add_app_launcher_args() 后，再使用 "
      "argparse.ArgumentParser.parse_args() "
      "生成 argparse.Namespace，并将结果直接传给 AppLauncher。",
      "以上只是向 AppLauncher 提供参数的一种方式；其他用法请参阅其 API 文档。",
    ),
    "understanding-the-output-of-help": (
      "执行脚本时传入 --help，可以同时查看脚本自定义参数和 AppLauncher 参数。",
      "输出中会列出脚本直接定义的 --size、--height 和 --width，以及由 "
      "AppLauncher 添加的其他参数。",
      "帮助信息前的 [INFO] 消息还会指出哪些参数将交给 SimulationApp。"
      "本例中的 --height 和 --width 与 SimulationApp 支持的名称和类型匹配，"
      "因此会自动转交。更多示例请参阅 SimulationApp 配置说明。",
    ),
    "using-environment-variables": (
      "AppLauncher 的 --livestream、--headless 等参数都有对应的环境变量。"
      "通过 CLI 传入参数，与在运行脚本前设置相应环境变量具有相同效果。",
      "环境变量适合保存跨会话使用的默认配置，例如写入 ${HOME}/.bashrc。"
      "如果同时提供 CLI 参数和环境变量，则 CLI 参数优先。",
      "这些参数适用于大多数通过 AppLauncher 启动的脚本。需要注意的是，"
      "--enable_cameras 会启用 Off-Screen Renderer，并且只兼容 "
      "isaaclab.sim.SimulationContext，不适用于 Isaac Sim 原生的 "
      "isaacsim.core.api.simulation_context.SimulationContext。",
    ),
    "the-code-explained@spawn_prims.html": (
      "Omniverse 使用 USD（Universal Scene Description）组织 Scene。USD 既是"
      "文件格式，也是一套用于分层描述 3D Scene 的系统，其层级结构类似文件系统。"
      "如果需要了解完整机制，建议阅读 USD 官方文档。",
      "理解本教程前，需要先掌握以下几个 USD 基本概念。",
      "Prim、Attribute 和 Relationship 共同组成 USD Stage。可以把 Stage 理解为"
      "容纳 Scene 中全部 Prim 的容器；设计 Scene，本质上就是构建 USD Stage。",
      "直接使用 USD API 灵活度很高，但学习和使用成本也较高。Isaac Lab 因此在"
      " USD API 之上提供由 Configuration 驱动的 Prim 生成接口，相关实现位于 "
      "sim.spawners Module。",
      "生成 Prim 时，需要创建相应的 Configuration Class 实例，用于描述 Prim "
      "的属性、材质及其他关系。随后将该配置、目标 Prim Path 和 Transform 传给"
      "对应的 Spawner Function，由其把 Prim 添加到 Scene。",
      "从整体上看，调用流程如下：",
      "本教程将演示多种 Prim 的生成方式。有关全部 Spawner，请参阅 Isaac Lab "
      "中的 sim.spawners Module。",
    ),
    "spawning-a-ground-plane": (
      "GroundPlaneCfg 用于配置网格状 Ground Plane，可以设置尺寸和外观等属性。",
    ),
    "spawning-lights": (
      "Stage 支持生成 Distant Light、Sphere Light、Disk Light 和 Cylinder Light "
      "等多种 Light Prim。本教程使用 Distant Light；它位于无限远处，并沿固定"
      "方向照亮整个 Scene。",
    ),
    "spawning-primitive-shapes": (
      "生成基本几何体前，需要先了解 Transform Prim（Xform）。Xform 只保存"
      "变换属性，可以把多个子 Prim 组织为一组，并对整组应用 Transform。"
      "本例创建一个 Xform，用于归组后续生成的几何体。",
      "接着使用 ConeCfg 生成圆锥体。Configuration 可以设置半径、高度、"
      "物理属性和 Material；默认不启用物理与 Material 属性。",
      "前两个圆锥体 Cone1 和 Cone2 仅用于显示，因此没有启用物理属性。",
      "第三个圆锥体 ConeRigid 通过 Configuration 启用 Rigid Body Physics。"
      "这些属性可用于设置质量、摩擦和恢复系数；未指定时使用 USD Physics 默认值。",
      "最后生成带 Deformable Body Physics 的长方体 CuboidDeformable。"
      "Deformable Body 的顶点可以相对运动，适合模拟布料、橡胶或果冻等 Soft "
      "Body。该功能仅支持 GPU Simulation，并要求 Mesh 配置相应物理属性。",
    ),
    "spawning-from-another-file": (
      "Prim 也可以从 USD、URDF 或 OBJ 等文件加载或转换。本教程把一个 Table "
      "USD Asset 加入 Scene；其 Mesh、Material 等信息均保存在 USD 文件中。",
      "该 Table 以 Reference 方式加入 Scene，即 Stage 保存的是指向 Asset 的"
      "引用，而不是复制全部内容。这样可以非破坏性地修改或覆盖 Material 等属性，"
      "而无需改写原始 Asset 文件。",
    ),
    "the-code-explained@add_new_robot.html": (
      "从本质上说，Robot 是带有关节驱动器的 Articulation。要让 Robot 在 "
      "Simulation 中运动，需要向驱动器发送目标值并推进 Simulation。直接管理"
      "各个关节驱动器十分繁琐，尤其是在控制复杂 Robot 或并行复制多个 "
      "Environment 时。",
      "Isaac Lab 使用一组 Configuration Class 描述 Robot Asset，例如需要复制"
      "哪些 USD Prim、哪些关节由 Agent 控制，以及执行 Reset 时应恢复到什么"
      "状态。具体配置取决于 Robot 所需的控制精度。本教程使用两个示例：Jetbot "
      "采用最小配置，Dofbot 则额外配置物理属性和初始状态。",
      "Jetbot 是顶部带有 Camera 的双轮差速 Robot。由于其 USD Asset 已由 "
      "Isaac Sim 提供，接入 Isaac Lab 时只需用 ArticulationCfg 描述该 Robot。",
      "这是 Isaac Lab 中最精简的 Robot Configuration，只包含 spawn 和 "
      "actuators 两个参数。",
      "spawn 参数接收 SpawnerCfg，用于指定描述 Robot 的 USD Asset。"
      "isaaclab.sim 提供的 USDFileCfg 可以根据 USD 文件路径生成所需的 "
      "SpawnerCfg；本例使用 Isaac Sim Assets 中的 "
      "<code>Robots/Jetbot/jetbot.usd</code>。这里的 <code>configuration</code> 即 "
      "Robot 的生成配置，文件名为 <code>jetbot.usd</code>。",
      "actuators 是执行器 Configuration 的字典，用于指定 Agent 控制 Robot 的"
      "哪些关节，以及采用何种执行器模型。Isaac Lab 提供多种常见执行器模型，"
      "也支持自定义实现。本例的车轮使用 ImplicitActuatorCfg，并沿用 USD Asset "
      "中的默认参数。",
      "actuators 字典的键是匹配关节名称的正则表达式。Jetbot 的关节较少，且"
      "全部使用相同配置，因此用 .* 匹配所有关节；也可以使用多个表达式为不同"
      "关节组指定不同配置。",
      "除上述最小配置外，还可以按需指定更多参数。",
      "Dofbot 是具有多个关节的简易机械臂，因此配置项更多。与 Jetbot 相比，"
      "主要增加了物理属性和初始状态 init_state。",
      "USDFileCfg 可以配置 Rigid Body 和 Articulation 的物理属性。rigid_props "
      "接收 RigidBodyPropertiesCfg，用于描述各 Link 作为 Rigid Body 时的行为；"
      "articulation_props 接收 ArticulationRootPropertiesCfg，用于设置求解器等"
      "与关节仿真相关的属性。isaaclab.sim.schemas 还提供其他可选的物理配置。",
      "ArticulationCfg 的 init_state 参数定义 Robot 在生成或 Reset 时使用的"
      "初始状态。joint_pos 是以 USD 关节名称为键的字典，而不是以执行器名称"
      "为键。pos 使用 Environment 局部坐标系，因此 (0.25, -0.25, 0.0) 表示"
      "相对 Environment Origin 的偏移，而不是相对世界坐标原点。",
      "完成两个 Robot 的 Configuration 后，即可在 Direct Workflow 中通过"
      "包含相应 Articulation Configuration 的 InteractiveSceneCfg 将它们加入"
      " Scene。",
      "随后推进 Simulation，并在每个 Step 中正确更新 Scene 实体。",
    ),
    "the-code-explained@run_rigid_object.html": (
      "该 Script 将 main() 拆分为两个函数，对应 Simulator 设置流程中的两个"
      "主要步骤：设计 Scene，以及运行 Simulation Loop。",
      "之所以分为两个步骤，是因为必须先完成 Scene 设计，再对 Simulator 执行 "
      "Reset。Reset 会自动开始 Simulation；此后不应再向 Scene 添加启用物理的"
      "新 Prim，否则可能出现意外行为，但仍可通过已有的 Physics Handle 与 Prim "
      "交互。",
    ),
    "designing-the-scene@run_rigid_object.html": (
      "与前面的教程一样，首先向 Scene 添加 Ground Plane 和 Light，再通过 "
      "assets.RigidObject 创建 Rigid Object。该 Class 会在指定路径生成 Prim，"
      "并初始化对应的 Rigid Body Physics Handle。",
      "本例沿用生成 Prim 教程中的圆锥体配置，但将 Spawn Configuration 包装在 "
      "assets.RigidObjectCfg 中。该配置描述 Asset 的生成方式、默认初始状态及"
      "其他元数据；传给 assets.RigidObject 后，会在 Simulation 开始时生成 "
      "Object 并初始化 Physics Handle。",
      "为演示一次生成多个 Rigid Object，代码先创建 /World/Origin{i} 形式的父 "
      "Xform Prim。向 assets.RigidObject 传入正则路径 /World/Origin.*/Cone 后，"
      "每个匹配的 Origin 下都会生成一个 Rigid Object Prim。例如，若 Scene 中"
      "存在 /World/Origin1 和 /World/Origin2，则会分别生成 "
      "/World/Origin1/Cone 和 /World/Origin2/Cone。",
      "由于后续 Simulation Loop 需要与该 Rigid Object 交互，Scene 创建函数会"
      "返回对应实体。后续教程将介绍如何用 scene.InteractiveScene 更方便地管理"
      "多个 Scene 实体。",
    ),
    "running-the-simulation-loop@run_rigid_object.html": (
      "Simulation Loop 包含三个步骤：按固定间隔重置 Simulation 状态、推进 "
      "Simulation，以及更新 Rigid Object 的内部 Buffer。为便于阅读，代码先从 "
      "Scene 实体字典中取出 Rigid Object 并保存到变量中。",
    ),
    "resetting-the-simulation-state@run_rigid_object.html": (
      "重置 Rigid Object Prim 时，需要同时设置 Pose 和 Velocity，两者共同构成"
      "根状态。该状态使用 Simulation World Frame，而不是父 Xform Prim 的局部"
      "坐标系，因为 Physics Engine 只识别 World Frame。因此，写入状态前必须先"
      "把目标状态转换到 World Frame。",
      "assets.RigidObject.data.default_root_state 提供默认根状态，其值可通过 "
      "assets.RigidObjectCfg.init_state 配置。本例在默认状态基础上随机修改平移，"
      "再调用 assets.RigidObject.write_root_pose_to_sim() 和 "
      "assets.RigidObject.write_root_velocity_to_sim()，将目标状态写入 Simulation "
      "Buffer。",
    ),
    "stepping-the-simulation@run_rigid_object.html": (
      "推进 Simulation 前，先调用 assets.RigidObject.write_data_to_sim() 将外力等"
      "待处理数据写入 Simulation Buffer。本教程没有施加外力，因此该调用并非"
      "必需，但为了展示完整流程仍予以保留。",
    ),
    "updating-the-state@run_rigid_object.html": (
      "每次推进 Simulation 后，调用 assets.RigidObject.update() 更新 Rigid "
      "Object 的内部 Buffer，使 assets.RigidObject.data 反映最新状态。",
    ),
    "designing-the-scene@run_articulation.html": (
      "与前面的教程一样，Scene 中包含 Ground Plane 和 Distant Light。不同之处"
      "在于，本例从 USD 文件生成 Cartpole Articulation，而不是 Rigid Object。"
      "Cartpole 由可沿 x 轴移动的滑车和可绕滑车旋转的杆组成；USD 文件保存其"
      "几何体、关节及其他物理属性。",
      "Cartpole 使用预定义的 assets.ArticulationCfg。该 Configuration Object "
      "包含生成方式、默认初始状态、各关节的执行器模型及其他元数据。有关创建"
      "此类配置的详细说明，请参阅“编写 Asset Configuration”教程。",
      "与 Rigid Object 类似，将 Configuration Object 传给 assets.Articulation "
      "构造函数，即可在 Scene 中生成并创建 Articulation 实例。",
    ),
    "running-the-simulation-loop@run_articulation.html": (
      "Simulation Loop 会定期重置 Simulation，向 Articulation 设置 Command，"
      "推进 Simulation，并更新 Articulation 的内部 Buffer。",
    ),
    "resetting-the-simulation@run_articulation.html": (
      "与 Rigid Object 一样，Articulation 也有描述根刚体的根状态；此外还有由"
      "各关节 Position 和 Velocity 组成的关节状态。",
      "重置时，先调用 Articulation.write_root_pose_to_sim() 和 "
      "Articulation.write_root_velocity_to_sim() 设置根状态，再调用 "
      "Articulation.write_joint_state_to_sim() 设置关节状态。最后调用 "
      "Articulation.reset() 清空内部 Buffer 和缓存。",
    ),
    "stepping-the-simulation@run_articulation.html": (
      "向 Articulation 应用 Command 分为两个步骤：",
      "本教程使用关节力矩 Command 控制 Articulation。为此，需要把 Articulation "
      "的 Stiffness 和 Damping 设为零；Cartpole 的预定义 Configuration 已完成"
      "这一设置。",
      "每个 Step 随机采样关节力矩，并通过 "
      "Articulation.set_joint_effort_target() 设置目标。随后调用 "
      "Articulation.write_data_to_sim() 将数据写入 PhysX Buffer，最后推进 "
      "Simulation。",
    ),
    "updating-the-state@run_articulation.html": (
      "每个 Articulation 都包含一个 assets.ArticulationData Object，用于保存"
      "自身状态。调用 assets.Articulation.update() 可从 Simulation 更新其中的 "
      "Buffer。",
    ),
    "designing-the-scene@run_deformable_object.html": (
      "与 Rigid Object 教程类似，Scene 中包含 Ground Plane 和 Light。此外，"
      "本例使用 assets.DeformableObject 添加 Deformable Object。该 Class 会在"
      "指定路径生成 Prim，并初始化对应的 Deformable Body Physics Handle。",
      "本例的软立方体使用与“生成 Prim”教程相似的 Spawn Configuration，只是"
      "进一步将它包装在 assets.DeformableObjectCfg 中。该配置描述 Asset 的"
      "生成方式和默认初始状态；将其传给 assets.DeformableObject 后，会在 "
      "Simulation 开始时生成 Object 并初始化 Physics Handle。",
      "与 Rigid Object 相同，将 Configuration Object 传给 "
      "assets.DeformableObject 构造函数，即可在 Scene 中生成并创建 "
      "Deformable Object 实例。",
    ),
    "running-the-simulation-loop@run_deformable_object.html": (
      "Simulation Loop 会按固定间隔重置 Simulation、向 Deformable Object 应用"
      "运动学 Command、推进 Simulation，并更新其内部 Buffer。",
    ),
    "resetting-the-simulation-state@run_deformable_object.html": (
      "与 Rigid Body 和 Articulation 不同，Deformable Object 的状态由 Mesh "
      "节点的 Position 和 Velocity 表示。这些值位于 Simulation World Frame，"
      "并保存在 assets.DeformableObject.data 中。",
      "assets.DeformableObject.data.default_nodal_state_w 提供所生成 Prim 的"
      "默认节点状态。该状态可通过 assets.DeformableObjectCfg.init_state 配置；"
      "本教程沿用默认值。",
      "代码对节点 Position 应用随机 Transform，从而随机化 Deformable Object "
      "的初始状态。",
      "重置时，先调用 assets.DeformableObject.write_nodal_state_to_sim() 将"
      "节点状态写入 Simulation Buffer，再调用 "
      "assets.DeformableObject.write_nodal_kinematic_target_to_sim() 清除上一轮 "
      "Simulation 中的运动学目标。下一节将说明运动学目标的作用。",
      "最后调用 assets.DeformableObject.reset() 清空内部 Buffer 和缓存。",
    ),
    "stepping-the-simulation@run_deformable_object.html": (
      "Deformable Body 支持部分运动学控制：用户可以为部分 Mesh 节点指定 Position "
      "目标，其余节点仍由 FEM Solver 模拟。这适合以可控方式操作 Deformable "
      "Object 的场景。",
      "本教程对四个立方体中的两个应用运动学 Command：设置索引为 0 的左下角"
      "节点，使其目标位置沿 z 轴移动。",
      "每个 Step 都会小幅增加该节点的运动学 Position 目标，并设置 Flag，表明"
      "该值是节点在 Simulation Buffer 中的运动学目标。随后调用 "
      "assets.DeformableObject.write_nodal_kinematic_target_to_sim() 写入目标。",
      "与 Rigid Object 和 Articulation 类似，推进 Simulation 前会调用 "
      "assets.DeformableObject.write_data_to_sim()。目前该 Method 不会向 "
      "Deformable Object 施加外力，但为了保持流程完整并便于后续扩展，示例仍"
      "保留此调用。",
    ),
    "updating-the-state@run_deformable_object.html": (
      "每次推进 Simulation 后，调用 assets.DeformableObject.update() 更新内部 "
      "Buffer，使 assets.DeformableObject.data 反映最新状态。",
      "示例按固定间隔在 Terminal 输出 Deformable Object 的 Root Position。"
      "Deformable Object 本身没有根状态，因此这里将全部 Mesh 节点 Position 的"
      "平均值视为 Root Position。",
    ),
    "designing-the-scene@run_surface_gripper.html": (
      "与前面的教程一样，Scene 中包含 Ground Plane 和 Distant Light。本例从 "
      "USD 文件生成一台三轴 Pick-and-Place Robot：龙门机构可沿 x、y、z 三个"
      "方向移动，末端执行器装有 Surface Gripper。USD 文件包含 Robot 的几何体、"
      "关节、物理属性和 Surface Gripper。若要为自己的 Robot 添加类似 Gripper，"
      "建议先查看 Isaac Lab Nucleus 中该 Asset 的 USD 文件。",
      "Robot 使用预定义的 Configuration Object；Surface Gripper 则需要创建 "
      "assets.SurfaceGripperCfg，并传入相应参数。",
      "可用参数如下：",
      "将 Robot Configuration 传给 assets.Articulation 构造函数即可创建 "
      "Articulation；Surface Gripper 的创建方式相同，将配置传给 "
      "assets.SurfaceGripper 构造函数后即可加入 Scene。实际初始化会在按下 "
      "Play、Simulation 开始运行时完成。",
    ),
    "running-the-simulation-loop@run_surface_gripper.html": (
      "Simulation Loop 会定期重置 Simulation，向 Articulation 和 Surface "
      "Gripper 设置 Command，推进 Simulation，并更新内部 Buffer。",
    ),
    "resetting-the-simulation@run_surface_gripper.html": (
      "重置 Surface Gripper 时，只需调用 SurfaceGripper.reset() 清空内部 "
      "Buffer 和缓存。",
    ),
    "stepping-the-simulation@run_surface_gripper.html": (
      "向 Surface Gripper 应用 Command 分为两个步骤：",
      "本教程使用随机 Command 控制 Gripper，其行为如下：",
      "每个 Step 随机采样 Command，并通过 "
      "SurfaceGripper.set_grippers_command() 发送给 Gripper。设置目标后，调用 "
      "SurfaceGripper.write_data_to_sim() 将数据写入 PhysX Buffer，最后推进 "
      "Simulation。",
    ),
    "updating-the-state@run_surface_gripper.html": (
      "可以通过 assets.SurfaceGripper.state() Property 查询当前状态。它返回形状为 "
      "[num_envs] 的 Tensor，每个元素为 -1、0 或 1，分别表示对应 Gripper 的"
      "状态。每次调用 assets.SurfaceGripper.update() 时都会更新该 Property。",
    ),
    "the-code-explained@create_scene.html": (
      "整体代码与前面的教程相似，但有几个关键差异，下面将逐一说明。",
    ),
    "scene-configuration": (
      "Scene 由多个实体组成，每个实体都有自己的 Configuration。这些配置定义在"
      "继承 scene.InteractiveSceneCfg 的 Configuration Class 中，再将其实例传给 "
      "scene.InteractiveScene 构造函数来创建 Scene。",
      "Cartpole 示例包含与上一教程相同的 Scene 实体，但现在统一声明在 "
      "CartpoleSceneCfg 中，而不再手动逐个生成。",
      "Configuration Class 中的变量名就是访问 Scene 实体时使用的键。例如，可用 "
      "scene[\"cartpole\"] 取得 Cartpole。后文会进一步说明访问方式；这里先介绍"
      "各类实体的配置。",
      "Rigid Object 和 Articulation 仍使用各自的 Configuration Class。Ground "
      "Plane 和 Light 属于非交互式 Prim，使用 assets.AssetBaseCfg；Cartpole 是"
      "交互式 Articulation，使用 assets.ArticulationCfg。非交互式 Prim（既不是 "
      "Asset，也不是 Sensor）不会由 Scene 在每个 Simulation Step 中更新。",
      "另一个重要区别是不同 Prim 的路径写法：",
      "Omniverse 在 USD Stage 中以层级图组织 Prim，Prim Path 表示其在图中的位置。"
      "Ground Plane 和 Light 使用绝对路径；Cartpole 使用包含 ENV_REGEX_NS 的"
      "相对路径。创建 Scene 时，该变量会替换为 /World/envs/env_{i} 形式的 "
      "Environment Namespace，因此路径中包含 ENV_REGEX_NS 的实体会被复制到每个 "
      "Environment。",
    ),
    "scene-instantiation": (
      "现在不再调用 design_scene() 手动创建 Scene，而是实例化 "
      "scene.InteractiveScene，并传入 CartpoleSceneCfg。创建 Configuration 时，"
      "num_envs 参数指定 Environment 副本数量，Scene 会据此完成克隆。",
    ),
    "accessing-scene-elements": (
      "可以通过 [] 运算符从 InteractiveScene 取得实体。运算符接收字符串键，并"
      "返回 Configuration Class 中同名的实体；例如键 \"cartpole\" 对应 Cartpole。",
    ),
    "running-the-simulation-loop@create_scene.html": (
      "Script 的其余部分与前面的示例基本相同。主要差别是原先直接调用 "
      "assets.Articulation Method 的位置，改为调用以下 InteractiveScene Method：",
      "scene.InteractiveScene 会在内部对 Scene 中的相应实体调用这些 Method。",
    ),
    "the-code-explained@create_manager_base_env.html": (
      "envs.ManagerBasedEnv 封装了与 Simulation 交互时的大部分细节，为用户提供"
      "简洁统一的 Environment Interface。它由以下组件组成：",
      "只需重新配置这些组件，便可用较少改动创建同一 Environment 的不同变体。"
      "本教程将介绍 envs.ManagerBasedEnv 以及新 Environment 的配置方法。",
    ),
    "designing-the-scene@create_manager_base_env.html": (
      "创建 Environment 的第一步是配置 Scene。Cartpole Environment 沿用上一"
      "教程的 Scene，因此这里不再重复代码；详细配置方式请参阅“使用 Interactive "
      "Scene”。",
    ),
    "defining-actions@create_manager_base_env.html": (
      "此前我们直接调用 assets.Articulation.set_joint_effort_target() 向 Cartpole "
      "发送 Action。本教程改用 managers.ActionManager 统一处理 Action。",
      "Action Manager 可以包含多个 managers.ActionTerm，每个 Action Term 负责"
      "控制 Environment 的一个部分。例如，机械臂可以分别使用一个 Term 控制手臂"
      "关节，另一个 Term 控制 Gripper，从而为不同组件采用不同的控制方式。",
      "在 Cartpole Environment 中，目标是控制施加在滑车上的力以保持杆的平衡，"
      "因此只需创建一个用于控制该作用力的 Action Term。",
    ),
    "defining-observations@create_manager_base_env.html": (
      "Scene 表示 Environment 的完整状态，Observation 则表示 Agent 能够观测到"
      "的部分。Agent 根据 Observation 决定采取什么 Action。在 Isaac Lab 中，"
      "Observation 由 managers.ObservationManager 计算。",
      "Observation Manager 可以包含多个 Observation Term，并将其划分为不同的 "
      "Observation Group，以定义不同的 Observation Space。例如，分层控制可以"
      "为底层 Controller 和高层 Controller 分别提供一个 Group。同一 Group 中"
      "的所有 Environment 必须具有相同维度。",
      "本教程只定义名为 \"policy\" 的 Observation Group。该名称虽非强制，但"
      "是 Isaac Lab 多种 Wrapper 的约定。Group 通过继承 "
      "managers.ObservationGroupCfg 定义，可统一设置是否加入 Noise，以及是否"
      "将各 Observation 拼接为单个 Tensor。",
      "每个 Observation Term 使用 managers.ObservationTermCfg 定义，其中 "
      "managers.ObservationTermCfg.func "
      "指定计算该 Observation 的 Function 或 Callable Class。还可以配置 Noise、"
      "Clipping 和 Scaling；本教程均使用默认值。",
    ),
    "defining-events@create_manager_base_env.html": (
      "至此已经定义 Cartpole Environment 的 Scene、Action 和 Observation。Event "
      "同样通过 Configuration Class 声明，再交给对应 Manager 处理。",
      "managers.EventManager 负责在特定时机修改 Simulation 状态，例如重置或"
      "随机化 Scene、随机化质量和摩擦等物理属性，以及修改颜色和纹理等视觉属性。"
      "每个 Event 由 managers.EventTermCfg 定义，其中 managers.EventTermCfg.func "
      "指定实际执行 Event "
      "的 Function 或 Callable Class。",
      "Event Term 还需要 mode，用于指定执行时机。也可以修改 ManagerBasedEnv "
      "以支持自定义 Mode；Isaac Lab 默认提供三种常用 Mode：",
      "本例在 Startup 时随机化杆的质量。该操作开销较高，只需执行一次；此外还"
      "定义一个 Reset Event，在每次重置时随机化滑车和杆的初始关节状态。",
    ),
    "tying-it-all-together@create_manager_base_env.html": (
      "完成 Scene 和各 Manager 的配置后，通过 envs.ManagerBasedEnvCfg 组合完整"
      "的 Environment Configuration，其中包含 Scene、Action、Observation 和 "
      "Event Configuration。",
      "envs.ManagerBasedEnvCfg.sim 还用于设置 Timestep、Gravity 等 Simulation "
      "参数。它已提供默认值；如需修改，建议在 Configuration 初始化后自动调用"
      "的 __post_init__() Method 中完成。",
    ),
    "running-the-simulation@create_manager_base_env.html": (
      "多数细节已经封装到 Environment Configuration 中，因此 Simulation Loop "
      "非常简洁：调用 envs.ManagerBasedEnv.reset() 重置 Environment，调用 "
      "envs.ManagerBasedEnv.step() 推进一步。两者都会返回 Observation 和 Info "
      "字典，后者可包含供 Agent 决策使用的附加信息。",
      "envs.ManagerBasedEnv 不包含 Termination 概念，因为 Termination 取决于具体"
      "的 Episodic Task。用户需要自行定义终止条件；本教程仅按固定间隔重置 "
      "Simulation。",
      "整个 Simulation Loop 放在 torch.inference_mode() Context Manager 中。"
      "Environment 内部使用 PyTorch 运算，但推理过程不需要梯度；关闭 Autograd "
      "可避免不必要的计算和内存开销。",
    ),
    "the-code-explained@create_manager_rl_env.html": (
      "“创建 Manager-Based Base Environment”教程已经说明如何配置 Scene、"
      "Observation、Action 和 Event，因此本节只介绍与 RL Task 相关的组件。",
      "Isaac Lab 在 envs.mdp Module 中提供了多种常用 Term。本教程会使用其中一"
      "部分，用户也可以在 Task 专属子 Package 中实现自己的 Term，例如 "
      "isaaclab_tasks.manager_based.classic.cartpole.mdp。",
    ),
    "defining-rewards": (
      "managers.RewardManager 负责计算 Agent 的 Reward。每个 Reward Term 使用 "
      "managers.RewardTermCfg 配置，其中包含计算 Reward 的 Function 或 Callable "
      "Class、对应权重，以及调用 Reward Function 时传入的 \"params\" 字典。",
      "Cartpole Task 使用以下 Reward Term：",
    ),
    "defining-termination-criteria": (
      "多数学习 Task 以有限长度的 Episode 运行。以 Cartpole 为例，目标是尽可能"
      "长时间保持杆的平衡；当系统进入不稳定或不安全状态时，应提前终止 Episode。"
      "即使 Agent 持续保持平衡，也会在达到时间上限后开始新 Episode，使其能够"
      "从不同初始状态继续学习。",
      "managers.TerminationsCfg 定义 Episode 的终止条件。本例在满足以下任一"
      "条件时终止：",
      "managers.TerminationsCfg.time_out Flag 用于区分超时导致的 Truncation "
      "和真正的 Termination；两者的含义与 Gymnasium 文档一致。",
    ),
    "defining-commands": (
      "对于具有目标条件的 Task，可以用 managers.CommandManager 为 Agent 生成"
      "目标或 Command。Command Manager 负责在每个 Step 更新和重新采样 Command，"
      "也可以将 Command 作为 Observation 提供给 Agent。",
      "本教程的 Task 不需要 Command，因此保留默认值 None。其他 Locomotion 或 "
      "Manipulation Task 中可以找到 Command Manager 的配置示例。",
    ),
    "defining-curriculum": (
      "训练 Agent 时，常从简单目标开始，并随训练进展逐步提高 Task 难度，这就是 "
      "Curriculum Learning。Isaac Lab 提供 managers.CurriculumManager 来配置此"
      "过程。",
      "为保持示例简单，本教程不使用 Curriculum；其他 Locomotion 和 Manipulation "
      "Task 中提供了相关示例。",
    ),
    "tying-it-all-together@create_manager_rl_env.html": (
      "定义上述组件后，即可创建 Cartpole 的 ManagerBasedRLEnvCfg。它与“创建 "
      "Manager-Based Base Environment”中的 ManagerBasedEnvCfg 类似，但额外"
      "包含前述 RL 组件。",
    ),
    "running-the-simulation-loop@create_manager_rl_env.html": (
      "run_cartpole_rl_env.py 的 Simulation Loop 与上一教程基本相同，区别是创建 "
      "envs.ManagerBasedRLEnv，而不是 envs.ManagerBasedEnv。因此，"
      "envs.ManagerBasedRLEnv.step() 还会返回 Reward 和 Termination 状态；Info "
      "字典中则记录各 Reward Term 的贡献、各 Term 的终止状态和 Episode Length "
      "等信息。",
    ),
    "the-code-explained@create_direct_rl_env.html": (
      "与 Manager-Based Environment 相同，Direct Workflow 也使用 Configuration "
      "Class 保存 Simulation、Scene、Actor 和 Task 设置，其基类是 "
      "envs.DirectRLEnvCfg。由于 Direct Workflow 不使用 Action Manager 和 "
      "Observation Manager，Task Configuration 需要直接声明 Action 和 "
      "Observation 的维度。",
      "Configuration Class 还可以保存 Reward 缩放系数、Reset 阈值等 Task 专属"
      "参数。",
      "创建 Environment 时，需要定义继承 envs.DirectRLEnv 的新 Class。",
      "该 Class 可以保存供各 Method 共用的成员变量，例如应用 Action、判断 Reset、"
      "计算 Reward 和构造 Observation 时所需的数据。",
    ),
    "scene-creation@create_direct_rl_env.html": (
      "Manager-Based Workflow 由 Framework 创建 Scene；Direct Workflow 则允许"
      "用户自行实现。_setup_scene(self) 中需要完成的工作包括：向 Stage 添加 "
      "Actor、克隆 Environment、过滤 Environment 之间的 Collision、将 Actor 注册"
      "到 Scene，以及添加 Ground Plane 和 Light 等其他 Prim。",
    ),
    "defining-rewards@create_direct_rl_env.html": (
      "_get_rewards(self) API 负责计算并返回 Reward Buffer。Task 可以在其中自由"
      "实现 Reward 逻辑；本例使用 PyTorch JIT Function 计算各个 Reward 分量。",
    ),
    "defining-observations@create_direct_rl_env.html": (
      "_get_observations(self) 负责构造 Observation Buffer。它应返回字典，其中 "
      "policy 键对应完整的 Policy Observation；对于 Asymmetric Policy，还应提供 "
      "critic 键及对应的 State Buffer。",
    ),
    "computing-dones-and-performing-resets@create_direct_rl_env.html": (
      "<code>_get_dones(self)</code> 负责填充 <code>dones</code> Buffer，判断哪些 "
      "Environment 应当 Reset，以及哪些 Environment "
      "达到 Episode Length 上限。它以两个 Boolean Tensor 组成的 Tuple 返回结果。",
      "得到待重置的 Environment 索引后，_reset_idx(self, env_ids) 会对其执行 Reset，"
      "并把新的状态直接写入 Simulation。",
    ),
    "applying-actions@create_direct_rl_env.html": (
      "Action 处理包含两个 API。_pre_physics_step(self, actions) 接收 Policy 输出"
      "的 Action，每个 RL Step 在所有 Physics Step 之前调用一次，可用于处理 Action "
      "Buffer 并将结果缓存为 Environment 成员变量。",
      "_apply_action(self) 在每个 RL Step 内按 decimation 次数调用，即每个 Physics "
      "Step 前调用一次，从而可以灵活决定每个 Physics Step 实际应用的 Action。",
    ),
    "the-code-explained@register_rl_env_gym.html": (
      "envs.ManagerBasedRLEnv 继承 gymnasium.Env 并遵循其标准 Interface。与传统 "
      "Gymnasium Environment 不同，它是 Vectorized Environment：同一进程会并行"
      "运行多个 Environment 实例，所有数据均以 Batch 形式返回。",
      "Direct Workflow 的 envs.DirectRLEnv 同样继承 gymnasium.Env。"
      "envs.DirectMARLEnv 虽不继承 Gymnasium，也可以采用相同方式注册和创建。",
    ),
    "using-the-gym-registry": (
      "使用 gymnasium.register() 注册 Environment 时，需要提供 Environment ID、"
      "Environment Class 的 Entry Point，以及 Environment Configuration Class "
      "的 Entry Point。示例代码将 Gymnasium 导入为 <code>gym</code>。",
    ),
    "manager-based-environments": (
      "Manager-Based Cartpole Environment 在 "
      "isaaclab_tasks.manager_based.classic.cartpole 子 Package 中按如下方式注册：",
      "id 参数是 Environment 名称。按照约定，Isaac Lab Environment 使用 Isaac- "
      "前缀，便于在 Registry 中检索；其后通常依次包含 Task 和 Robot 名称。例如，"
      "ANYmal C 在平坦地形上的 Locomotion Environment 名为 "
      "Isaac-Velocity-Flat-Anymal-C-v0。<code>v&lt;N&gt;</code> 表示同一 Environment "
      "的不同版本，"
      "可避免名称过长。",
      "entry_point 指定 Environment Class，格式为 "
      "<code>&lt;module&gt;:&lt;class&gt;</code>。Cartpole 的"
      "值是 isaaclab.envs:ManagerBasedRLEnv；创建 Environment 实例时，Gymnasium "
      "会通过该字符串导入相应 Class。",
      "env_cfg_entry_point 指定默认 Environment Configuration。"
      "isaaclab_tasks.utils.parse_env_cfg() 会加载该配置，再把它传给 "
      "gymnasium.make()。Configuration Entry Point 可以指向 YAML 文件，也可以"
      "指向 Python Configuration Class。",
    ),
    "direct-environments@register_rl_env_gym.html": (
      "Direct Environment 的注册方式相似，但 Entry Point 指向具体 Environment "
      "实现 Class，而不是 ManagerBasedRLEnv。名称还会加入 -Direct 后缀，以便与 "
      "Manager-Based Environment 区分。",
      "下面是 isaaclab_tasks.direct.cartpole 子 Package 中 Cartpole Environment "
      "的注册方式：",
    ),
    "creating-the-environment": (
      "Script 开头需要导入 isaaclab_tasks Extension，让 Gymnasium Registry 获知"
      "其中提供的全部 Environment。导入会执行 __init__.py，遍历各子 Package 并"
      "完成相应注册。",
      "本教程从 Command Line 读取 Task 名称，用它解析默认 Configuration 并创建 "
      "Environment。Command Line 中的 Environment 数量、Simulation Device 和"
      "是否 Rendering 等参数，也会覆盖默认配置。",
      "Environment 创建完成后，其余流程遵循标准的 Reset 和 Step Interface。",
    ),
    "the-code-explained@add_sensors_on_robot.html": (
      "与 Asset 一样，Sensor 也通过 Scene Configuration 加入 Scene。所有 Sensor "
      "均继承 sensors.SensorBase，并由各自的 Configuration Class 配置。每个 "
      "Sensor 可以通过 sensors.SensorBaseCfg.update_period 单独设置更新周期，"
      "单位为秒。",
      "Sensor 会根据 Prim Path 和 Sensor 类型连接到 Scene。部分 Sensor 会创建"
      "自己的 Prim，例如 Camera；另一些则依附于现有 Prim，例如 Contact Sensor "
      "通过 Rigid Body Prim 上的 Contact Report API 工作。",
      "下面依次介绍本教程使用的 Sensor 及其配置方式。更多信息请参阅 sensors "
      "Module。",
    ),
    "camera-sensor": (
      "Camera 使用 sensors.CameraCfg 配置。它基于 USD Camera Sensor，并通过 "
      "Omniverse Replicator API 捕获不同类型的数据。Camera 有对应的 Prim，因此"
      "会在指定 Prim Path 处创建。",
      "Camera Sensor Configuration 包含以下参数：",
      "将 RGB-D Camera 安装到 Robot 头部时，需要给出它相对 Robot Base Frame "
      "的 Offset，包括 Translation、Rotation 及 <code>convention</code>。",
      "本教程将 Update Period 设为 0.1 s，即 Camera 以 10 Hz 更新。Prim Path 为 "
      "{ENV_REGEX_NS}/Robot/base/front_cam：{ENV_REGEX_NS} 表示 Environment "
      "Namespace，<code>\"Robot\"</code> 是 Asset 名称，<code>\"base\"</code> 是 "
      "Camera 所附着的 Prim，<code>\"front_cam\"</code> 是 Camera Sensor 对应的 "
      "Prim。",
    ),
    "height-scanner": (
      "Height Scanner 是使用 NVIDIA Warp Ray-Casting Kernel 实现的虚拟 Sensor。"
      "sensors.RayCasterCfg 用于指定 Ray Pattern 和被投射的 Mesh。由于它是虚拟 "
      "Sensor，Scene 中不会创建对应 Prim，而是依附到现有 Prim 来确定 Sensor "
      "位置。",
      "本教程将 Height Scanner 安装到 Robot Base Frame。pattern 属性定义 Ray "
      "Pattern，规则网格使用 GridPatternCfg。由于这里只关心高度，不需要考虑 "
      "Robot 的 Roll 和 Pitch，因此将 ray_alignment 设为 \"yaw\"。",
      "把 debug_vis 设为 True，可以显示 Ray 与 Mesh 的交点。",
      "完整的 Height Scanner Configuration 如下：",
    ),
    "contact-sensor": (
      "Contact Sensor 封装 PhysX Contact Report API，用于获取 Robot 与 Environment "
      "的接触信息。它要求在 Robot 的 Rigid Body 上启用该 API，可通过在 Asset "
      "Configuration 中将 activate_contact_sensors 设为 True 完成。",
      "sensors.ContactSensorCfg 用于指定需要监测的 Prim。还可以启用额外选项，"
      "获取接触与离地时间，或筛选特定 Prim 之间的接触力。",
      "本教程把 Contact Sensor 安装在 Robot 的四只脚上，名称分别为 LF_FOOT、"
      "\"RF_FOOT\"、\"LH_FOOT\" 和 \"RH_FOOT\"（首个名称为 \"LF_FOOT\"）。"
      "Prim Path 使用正则表达式 \".*_FOOT\"，一次匹配所有以 \"_FOOT\" 结尾的 "
      "Prim。",
      "Update Period 设为 0，表示 Sensor 与 Simulation 同频更新。Contact Sensor "
      "还可以保存历史数据；本例将 History Length 设为 6，保留最近 6 个 "
      "Simulation Step 的接触信息。",
      "完整的 Contact Sensor Configuration 如下：",
    ),
    "running-the-simulation-loop@add_sensors_on_robot.html": (
      "与 Asset 相同，Sensor 的 Buffer 和 Physics Handle 只会在 Simulation 开始"
      "时初始化，因此创建 Scene 后必须调用 sim.reset()。",
      "其余 Simulation Loop 与前面的教程相似。Sensor 随 Scene 一起更新，并按"
      "各自的 Update Period 管理内部 Buffer。",
      "Sensor 数据可通过 data Property 访问。下面演示如何读取本教程中各 Sensor "
      "的数据：",
    ),
    "the-code-explained@run_diff_ik.html": (
      "使用 Task-Space Controller 时，必须确保所有输入量都使用正确的 Coordinate "
      "Frame。并行 Environment 共处于同一个 Simulation World Frame，但通常希望"
      "每个 Environment 都拥有自己的 Local Frame；其 Origin 可通过 "
      "scene.InteractiveScene.env_origins 获取。",
      "Isaac Lab API 使用以下 Frame 记号：",
      "Asset 不感知 Environment Local Frame，因此返回的状态都位于 Simulation "
      "World Frame。使用这些状态前，需要减去对应的 Environment Origin，将其"
      "转换到 Environment Local Frame。",
    ),
    "creating-an-ik-controller": (
      "DifferentialIKController 根据目标末端执行器 Pose 计算 Robot 所需的关节 "
      "Position。该实现使用 PyTorch 批量计算，支持 Damped Least Squares、"
      "Pseudo-Inverse 等 IK Solver，可通过 ik_method 选择；Command 既可以是"
      "相对 Pose，也可以是绝对 Pose。",
      "本教程使用 Damped Least Squares 计算关节 Position，并用 Absolute Pose "
      "Command 跟踪目标末端执行器 Pose。",
    ),
    "obtaining-the-robot-s-joint-and-body-indices": (
      "IK Controller 只负责计算，因此需要用户提供 Robot 的关节 Position、当前"
      "末端执行器 Pose 和 Jacobian Matrix。",
      "assets.ArticulationData.joint_pos 包含全部关节，但这里只需要机械臂关节，"
      "不需要 Gripper；assets.ArticulationData.body_state_w 包含全部刚体状态，"
      "而这里只需要末端执行器。因此必须先取得相应索引。",
      "Articulation 提供 find_joints() 和 find_bodies()，可根据关节或刚体名称"
      "返回对应索引。",
      "也可以直接调用上述 Method，但更推荐使用 SceneEntityCfg 解析索引。该 "
      "Class 在内部调用这些 Method，并额外检查名称是否有效，因此更安全。",
    ),
    "computing-robot-command@run_diff_ik.html": (
      "IK Controller 将设置目标 Command 与计算关节 Position 分开，使 Controller "
      "可以按不同于 Robot 控制频率的频率运行。",
      "set_command() 接收批量形式的目标末端执行器 Pose，该 Pose 位于 Robot Base "
      "Frame。",
      "compute() 根据当前末端执行器 Pose、Jacobian 和关节 Position 计算目标关节 "
      "Position。Jacobian 从 Robot 数据中读取，其值由 Physics Engine 计算。",
      "最后，按照前面教程中的方式把计算得到的关节 Position 目标发送给 Robot。",
    ),
    "the-code-explained@run_rl_training.html": (
      "大部分代码用于创建 Log 目录、保存解析后的 Configuration，以及初始化 "
      "Stable-Baselines3 组件。本教程的重点是创建 Environment，并使用 "
      "Stable-Baselines3 Wrapper 对其进行封装。",
      "代码使用三个 Wrapper：",
      "每个 <code>gym</code> Wrapper 都以 env = wrapper(env, *args, **kwargs) 的形式"
      "逐层封装"
      "前一层。"
      "最终得到的 Environment 用于训练 Agent。更多说明请参阅“包装 "
      "Environment”文档。",
    ),
    "headless-execution@run_rl_training.html": (
      "传入 --headless 后，训练期间不进行 Rendering。这适用于远程服务器，也能"
      "避免只为观察画面而产生的开销；由于只执行 Physics Simulation Step，"
      "训练通常会更快。",
    ),
    "headless-execution-with-off-screen-render@run_rl_training.html": (
      "纯 Headless 模式不进行 Rendering，无法记录 Agent 的训练画面。传入 "
      "--enable_cameras 可启用 Off-Screen Rendering，再配合 --video 录制训练"
      "过程。",
      "视频保存在 "
      "<code>logs/sb3/Isaac-Cartpole-v0/&lt;run-dir&gt;/videos/train</code>，可使用任意"
      "视频播放器打开。",
    ),
    "creating-an-operational-space-controller": (
      "OperationalSpaceController 计算关节 Effort 或 Torque，使 Robot 能够在 Task "
      "Space 中同时执行 Motion Control 和 Force Control。",
      "Task Frame 可以是欧氏空间中的任意 Coordinate Frame，默认使用 Robot Base "
      "Frame。若在其他 Frame 中定义目标更方便，可通过 set_command() 的 "
      "current_task_frame_pose_b 参数提供 Task Frame 相对 Robot Base Frame 的 "
      "Pose。本教程把与墙面平行的 Frame 作为 Task Frame，这样接触力只需沿该 "
      "Frame 的 z 轴指定。OperationalSpaceControllerCfg 中的相关参数都应按此 "
      "Task Frame 理解。",
      "Motion Target 可以是相对 Robot Base 的 Absolute Pose（"
      "<code>target_types: \"pose_abs\"</code>），也可以是相对当前末端执行器 Pose "
      "的 Relative Pose（<code>target_types: \"pose_rel\"</code>）。Force Target "
      "使用 Absolute Wrench（<code>target_types: \"force_abs\"</code>）。"
      "同时控制 Pose 和 Force 时，target_types 可设为 [\"pose_abs\", "
      "\"wrench_abs\"] 或 [\"pose_rel\", \"wrench_abs\"]。",
      "motion_control_axes_task 和 force_control_axes_task 分别指定 Motion Control "
      "与 Force Control 所作用的轴。两个列表各包含六个 0 或 1，对应三条平移轴"
      "和三条旋转轴，并且必须互补。",
      "Motion Control 的 Stiffness 和 Damping Ratio 分别由 "
      "motion_control_stiffness 和 motion_damping_ratio_task 指定，可以是对所有"
      "轴生效的标量，也可以是六元素列表。若希望把这些值作为 Command 的一部分，"
      "可将 impedance_mode 设为 \"variable_kp\" 或 \"variable\"，并通过相应的 "
      "<code>motion_stiffness_limits_task</code> 和 "
      "<code>motion_damping_limits_task</code> 约束取值范围。",
      "Contact Force 可以采用 Open-Loop Control，也可以设置 "
      "contact_wrench_stiffness_task，使用包含 Feedforward Term 的 Closed-Loop "
      "Control。目前 Contact Sensor 只能测量线性 Contact Wrench，因此闭环控制"
      "只使用该参数的前三个元素。",
      "将 inertial_dynamics_decoupling 设为 True，可利用 Robot Inertia Matrix "
      "解耦 Task Space Acceleration，这对快速运动的控制精度尤其重要。若将 "
      "partial_inertial_dynamics_decoupling 设为 True，则忽略平移轴和旋转轴之间"
      "的惯性耦合。",
      "如需在 Operational Space Command 中加入 Gravity Compensation，可将 "
      "gravity_compensation 设为 True。",
      "冗余 Robot 还需要考虑 Null Space Control。Null Space 中的关节运动不会"
      "改变 Task Space Coordinate；如果不加约束，关节可能漂移甚至接近 Limit。"
      "将 nullspace_control 设为 \"position\" 可启用 Null-Space PD Controller，"
      "并通过 nullspace_stiffness 和 nullspace_damping_ratio 调整其行为。只有"
      "启用完整 Inertial Dynamics Decoupling（即相关选项不是 <code>False</code>）"
      "时，Null Space 与 Task Space 才能在理论上完全解耦；默认控制模式为 "
      "<code>\"none\"</code>。",
      "该 OSC 实现使用 PyTorch，以 Batch 形式完成计算。",
      "本教程用 \"pose_abs\" 控制除 z 轴外的 Motion，用 \"wrench_abs\" 控制 z "
      "轴 Force；启用完整 Inertial Decoupling，但不启用 Gravity Compensation，"
      "因为 Robot Configuration 已关闭 Gravity。Impedance Mode 设为 "
      "\"variable_kp\"，Null-Space Control 设为 \"position\"，目标关节 Position "
      "取关节 Limit 的中点。",
    ),
    "updating-the-states-of-the-robot": (
      "OSC 只负责计算，因此用户必须提供 Robot 的 Jacobian Matrix、Mass/Inertia "
      "Matrix、末端执行器 Pose 和 Velocity、Contact Force，以及关节 Position 和 "
      "Velocity；这些量都使用 Root Frame。若启用相应功能，还需提供 Gravity "
      "Compensation Vector 和 Null-Space Joint Position Target。",
    ),
    "computing-robot-command@run_osc.html": (
      "OSC 将设置目标 Command 与计算关节 Effort 分开。Command Vector 按 "
      "target_types 中的顺序包含各目标；当 impedance_mode 为 \"variable_kp\" 或 "
      "\"variable\" 时，还需附加 Stiffness 和 Damping Ratio。所有值都应位于同一 "
      "Task Frame，并按顺序拼接；代码以 <code>_task</code> 下标标识这些量。",
      "本教程先在 Task Frame 中定义目标 Wrench，再将目标 Pose 转换到 Task Frame：",
      "随后调用 OSC，传入 Task Frame 中的 Command Vector、Base Frame 中的末端"
      "执行器 Pose，以及 Task Frame 相对 Base Frame 的 Pose。OSC 内部会在 Base "
      "Frame 中完成计算。",
      "根据 Robot 状态和目标 Command 计算关节 Effort 或 Torque：",
      "最后将计算得到的关节 Effort 或 Torque 目标发送给 Robot。",
    ),
    "the-code-execution@launch_app.html": (
      "现在运行示例 Script：",
      "该 Command 会在 Simulation 中生成一个体积为 0.5 m³ 的长方体。由于 "
      "LIVESTREAM 环境变量隐含启用了 --headless，因此不会显示本地 GUI。需要"
      "查看画面时，可以使用 Isaac WebRTC Livestream；目前这是 Container 中"
      "支持的 Visualization 方式。按启动 Terminal 中的 Ctrl+C 可终止进程。",
      "接下来检查 AppLauncher 如何处理相互冲突的参数：",
      "运行结果与上一个 Command 相同。虽然环境变量设置了 LIVESTREAM=0，但 "
      "CLI 参数 --livestream 的优先级更高，因此最终仍会启用 Livestream。按 "
      "Ctrl+C 可终止进程。",
      "最后，通过 AppLauncher 向 SimulationApp 传递参数：",
      "运行行为仍与前面相同，但 Viewport 会以 1920 × 1080 分辨率 Rendering。"
      "采集高分辨率视频时可以提高该值；若更重视 Simulation 性能，则可以降低"
      "分辨率。按启动 Terminal 中的 Ctrl+C 可终止进程。",
    ),
    "the-code@configuring_rl_training.html": (
      "本例查看 isaaclab_tasks Package 中 Isaac-Cartpole-v0 Task 的 Configuration。"
      "这正是“使用 RL Agent 训练”教程所使用的 Task，其注册过程使用 "
      "<code>gymnasium.register</code>。",
    ),
    "executing-the-script@spawn_prims.html": (
      "与前面的教程一样，执行以下 Command 运行 Script：",
      "Simulation 启动后，窗口中会显示 Ground Plane、Light、多个圆锥体和一张"
      "桌子。启用 Rigid Body Physics 的绿色圆锥体会落下，并与桌面和 Ground "
      "Plane 发生 Collision；其余圆锥体只用于显示，不会移动。关闭窗口或在 "
      "Terminal 中按 Ctrl+C 即可停止 Simulation。",
      "本教程介绍了在 Isaac Lab Scene 中生成多种 Prim 的基本方法，并演示了 "
      "Scene 设计和 Spawner 的核心概念。下一节将进一步介绍如何与 Scene 和 "
      "Simulation 交互。",
    ),
    "the-base-code": (
      "本教程以 isaaclab_tasks.direct.humanoid Module 中的 Direct Workflow "
      "Humanoid Environment 为基础。",
    ),
    "duplicating-the-file-and-registering-a-new-task": (
      "为避免修改现有 Task，先复制其 Python 实现。在 Isaac Lab Project 的 "
      "source/isaaclab_tasks/isaaclab_tasks/direct/humanoid 目录中，将 "
      "humanoid_env.py 复制并重命名为 h1_env.py。",
      "用代码编辑器打开 h1_env.py，将 HumanoidEnv 和 HumanoidEnvCfg 分别重命名"
      "为 H1Env 和 H1EnvCfg，避免注册新 Environment 时发生导入名称冲突。",
      "然后修改同一目录中的 __init__.py，添加注册项，将新 Task 注册为 "
      "Isaac-H1-Direct-v0。Environment 注册机制详见“注册 Environment”教程。",
    ),
    "changing-the-robot": (
      "新文件中的 H1EnvCfg 封装 Environment Configuration，包括需要实例化的 "
      "Asset；其中 robot 属性保存目标 Articulation Configuration。",
      "Unitree H1 已包含在 Isaac Lab Assets Extension（isaaclab_assets）中，因此"
      "可以直接导入并替换 H1EnvCfg.robot。还需要修改 joint_gears，因为其中"
      "保存的是 Robot 专属配置。",
      "更换 Robot 后，受控关节数量和 Articulation 中的 Rigid Body 数量可能发生"
      "变化。因此还需按新 Robot 调整其他 Environment Configuration，例如 "
      "Observation Space 和 Action Space 的维度。",
    ),
    "the-code-explained@configuring_rl_training.html": (
      "kwargs 中保存各 RL Library 的 Configuration。键表示 Library 名称，值是"
      "配置入口，可以是字符串、Class 或 Class 实例。例如，"
      "\"rl_games_cfg_entry_point\" 指向 RL-Games 的 YAML 文件，"
      "\"rsl_rl_cfg_entry_point\" 则指向 RSL-RL 的 Configuration Class。",
      "Agent Configuration Entry Point 的写法与 Environment Configuration Entry "
      "Point 相似，因此下面两种形式等价：",
      "推荐使用第一个代码块中的字符串 Entry Point。第二种写法会在注册时直接"
      "导入 Configuration Class，从而增加导入时间。",
      "scripts/reinforcement_learning 下的 Script 默认从 kwargs 读取 "
      "<code>&lt;library_name&gt;_cfg_entry_point</code>，以取得对应 Configuration。",
      "下面演示 train.py 如何读取 Stable-Baselines3 Configuration：",
      "--agent 参数指定 RL Library，并用于从 kwargs 中选择 Configuration。也可"
      "通过该参数显式指定其他 Configuration Entry Point。",
    ),
    "the-tutorial-code": (
      "本教程使用由已训练 Policy Checkpoint 导出的 JIT 文件，即可脱离训练流程"
      "运行的 Policy 版本。",
      "H1RoughEnvCfg_PLAY 封装 Policy Inference 所需的 Environment "
      "Configuration，包括要实例化的 Asset。",
      "为了使用预先构建的 USD Environment，而不是 Configuration 中的 Terrain "
      "Generator，需要在把 Config 传给 ManagerBasedRLEnv 前进行以下修改。",
      "示例把 Device 设为 CPU，并在推理时关闭 Fabric。对于少量 Environment，"
      "CPU Simulation 通常比 GPU Simulation 更快。",
    ),
    "the-code-execution@run_rigid_object.html": (
      "代码完成后，执行以下 Command 查看结果：",
      "窗口中会显示 Ground Plane、Light 和多个绿色圆锥体。圆锥体从随机高度"
      "落下，并与地面发生 Collision。关闭窗口、单击 UI 中的 Stop 按钮，或在 "
      "Terminal 中按 Ctrl+C，均可停止 Simulation。该按钮在 UI 中标为 "
      "<code>STOP</code>。",
      "本教程演示了如何生成 Rigid Object，用 RigidObject Class 初始化其 Physics "
      "Handle，并读写 Object 状态。下一教程将介绍 Articulation，即由关节连接的"
      "多个 Rigid Object。",
    ),
    "the-code-execution@run_deformable_object.html": (
      "代码完成后，执行以下 Command 查看结果：",
      "窗口中会显示 Ground Plane、Light 和四个绿色软立方体。其中两个从高处"
      "落到地面，另外两个沿 z 轴移动；Marker 会显示左下角节点的运动学目标 "
      "Position。关闭窗口或在 Terminal 中按 Ctrl+C 可停止 Simulation。",
      "本教程演示了如何生成 Deformable Object，用 DeformableObject Class 初始化"
      "其 Physics Handle，读写 Object 状态，并通过运动学 Command 控制 Mesh 节点。"
      "下一教程将使用 InteractiveScene Class 创建 Scene。",
    ),
    "the-code-execution@create_scene.html": (
      "执行 Script，并通过 --num_envs 参数在 Scene 中模拟 32 个 Cartpole：",
      "窗口中会显示 32 个随机摆动的 Cartpole。可以用鼠标旋转 Camera，并使用"
      "方向键在 Scene 中移动。",
      "本教程介绍了如何用 scene.InteractiveScene 创建包含多个 Asset 的 Scene，"
      "以及如何通过 num_envs 克隆多个 Environment。",
      "isaaclab_tasks Extension 中的 Task 还提供了更多 "
      "scene.InteractiveSceneCfg 示例，可查阅 Source Code 了解复杂 Scene 的用法。",
    ),
    "the-code-execution@create_manager_base_env.html": (
      "执行以下 Command 运行本教程创建的基础 Environment：",
      "窗口中会显示 Ground Plane、Light 和多个 Cartpole，并向 Cartpole 应用随机 "
      "Action。屏幕右下角还会显示名为 \"Isaac Lab\" 的 UI，其中提供 Debugging "
      "和 Visualization 控件。",
      "关闭窗口或在启动 Simulation 的 Terminal 中按 Ctrl+C 即可停止。",
      "本教程介绍了构建基础 Environment 所需的各种 Manager。"
      "scripts/tutorials/03_envs 目录还包含更多基础 Environment 示例，可用下列 "
      "Command 运行：",
      "下一教程将介绍 envs.ManagerBasedRLEnv，以及如何用它创建 Markov Decision "
      "Process（MDP）。",
    ),
    "the-code-execution@create_manager_rl_env.html": (
      "与前面的教程相同，执行 run_cartpole_rl_env.py 运行 Environment：",
      "显示的 Simulation 与上一教程相似，但 Environment 现在还会返回 Reward 和 "
      "Termination 状态。每个 Environment 在满足 Configuration 中的终止条件时"
      "会独立 Reset。",
      "关闭窗口或在启动 Simulation 的 Terminal 中按 Ctrl+C 即可停止。",
      "本教程通过 Reward、Termination、Command 和 Curriculum Term 扩展基础 "
      "Environment，构建了用于 RL 的 Task Environment；还演示了如何运行 "
      "envs.ManagerBasedRLEnv 并读取其返回信号。",
      "虽然可以手动实例化 envs.ManagerBasedRLEnv，但为每个 Task 编写专用 Script "
      "并不便于扩展。下一教程将使用 gymnasium.make()，通过 Gymnasium Interface "
      "按名称创建 Environment。",
    ),
    "the-code-execution@register_rl_env_gym.html": (
      "代码完成后，执行以下 Command 查看结果：",
      "窗口中显示的内容与“创建 Manager-Based RL Environment”教程相似。关闭窗口"
      "或在 Terminal 中按 Ctrl+C 即可停止 Simulation。",
      "还可以通过 --device Flag 显式选择 Simulation Device：",
      "传入 --device cpu 后，Simulation 在 CPU 上运行，便于 Debugging，但速度会"
      "明显慢于 GPU Simulation。",
    ),
    "interactive-execution@run_rl_training.html": (
      "上述两种方式适合训练，但无法直接与画面交互。若要观察实时 Simulation，"
      "可省略 --headless，并按如下方式运行训练 Script：",
      "Isaac Sim 窗口会显示 Agent 在 Environment 中训练。实时 Rendering 会降低"
      "训练速度，可以使用屏幕右下角 \"Isaac Lab\" 面板切换 Render Mode。有关"
      "各模式的说明，请参阅 sim.SimulationContext.RenderMode。",
    ),
    "action-and-observation-noise": (
      "Direct Workflow 也可以通过 configclass Module 配置 Action Noise 和 "
      "Observation Noise。相应配置需要赋给主 Task Configuration 的 "
      "action_noise_model 和 observation_noise_model：",
      "NoiseModelWithAdditiveBiasCfg 可以同时生成每个 Step 独立采样的 Noise，"
      "以及在 Reset 时重新采样、并在整个 Episode 中保持相关性的 Bias Noise。",
      "noise_cfg Term 定义每个 Step 为所有 Environment 采样的 Gaussian "
      "Distribution，采样结果会分别加入 Action Buffer 和 Observation Buffer。",
      "bias_noise_cfg Term 定义在 Environment Reset 时采样的相关 Noise。该值在"
      "当前 Episode 的每个 Step 中保持不变，并在下一次 Reset 时重新采样。",
      "如果只需要 Per-Step Noise，可以使用 GaussianNoiseCfg，定义叠加到输入 "
      "Buffer 上的 Additive Gaussian Distribution。",
      "本教程通过扩展基础 Environment，实现了 Direct Workflow RL Task 所需的 "
      "Scene Setup、Action、Done、Reset、Reward 和 Observation Function。",
      "可以手动实例化 DirectRLEnv，但为每个 Task 编写专用 Script 并不便于扩展。"
      "下一教程将使用 gymnasium.make()，通过 Gymnasium Interface 创建 "
      "Environment。",
    ),
    "the-code-execution@add_sensors_on_robot.html": (
      "代码完成后，执行以下 Command 查看结果：",
      "窗口中会显示 Ground Plane、Light 和两台四足 Robot。Robot 周围的红色球体"
      "表示 Ray 与 Mesh 的交点。还可以切换 Viewport 的 Camera 视图，查看 Camera "
      "Sensor 捕获的图像；具体操作请参阅链接说明。",
      "关闭窗口或在 Terminal 中按 Ctrl+C 即可停止 Simulation。",
      "本教程介绍了多种 Sensor 的配置和使用方式。sensors Module 还提供其他 "
      "Sensor；scripts/tutorials/04_sensors 目录中包含最小示例，可用下列 Command "
      "运行：",
    ),
  }


# ===== Apply reviewed section prose ========================================= #
def _apply_reviewed_section_prose(tree, page_path):
  reviewed = _reviewed_section_prose()
  for heading in tree.xpath("//h2[@id] | //h3[@id] | //h4[@id]"):
    heading_id = heading.get("id")
    page_specific_key = f"{heading_id}@{page_path.name}"
    paragraphs = reviewed.get(page_specific_key, reviewed.get(heading_id))
    if not paragraphs:
      continue
    container = heading.getparent()
    existing_paragraphs = container.xpath("./p")
    for existing, replacement in zip(existing_paragraphs, paragraphs):
      _replace_paragraph(existing, replacement)


# ===== Find a matching translated section ================================== #
def _find_local_section(tree, section_id):
  sections = tree.xpath("//section[@id=$value]", value=section_id)
  if sections:
    return sections[0]
  sections = tree.xpath(
    "//section[./h2[@id=$value] or ./h3[@id=$value] or ./h4[@id=$value]]",
    value=section_id,
  )
  return sections[0] if sections else None


# ===== Wrap one matching text occurrence =================================== #
def _wrap_text_occurrence(paragraph, value, markup):
  text_nodes = paragraph.xpath(".//text()[not(ancestor::code)]")
  for text_node in text_nodes:
    current = str(text_node)
    offset = current.find(value)
    if offset < 0:
      continue
    fragment = html.fragment_fromstring(markup)
    before = current[:offset]
    after = current[offset + len(value):]
    owner = text_node.getparent()
    if text_node.is_text:
      owner.text = before
      owner.insert(0, fragment)
    else:
      parent = owner.getparent()
      owner.tail = before
      parent.insert(parent.index(owner) + 1, fragment)
    fragment.tail = after
    return True
  return False


# ===== Restore official inline-code markup ================================= #
def _restore_inline_code(tree, page_path):
  try:
    relative_path = page_path.relative_to(DOCUMENT_ROOT / "tutorials")
  except ValueError:
    return
  official_path = OFFICIAL_HTML_ROOT / relative_path
  if not official_path.exists():
    return
  official_page_url = urljoin(
    OFFICIAL_BASE_URL,
    f"source/tutorials/{relative_path.with_suffix('.html')}",
  )
  for link in tree.xpath("//article//a[@href]"):
    href = link.get("href", "")
    if href.startswith("../") and "/api/" in href:
      link.set("href", urljoin(official_page_url, href))
  official_tree = html.parse(str(official_path))
  for official_section in official_tree.xpath("//article//section[@id]"):
    section_id = official_section.get("id")
    local_section = _find_local_section(tree, section_id)
    if local_section is None:
      continue
    official_paragraphs = official_section.xpath("./p")
    local_paragraphs = local_section.xpath("./p")
    for official_paragraph, local_paragraph in zip(
        official_paragraphs, local_paragraphs):
      for code_element in official_paragraph.xpath(".//code"):
        value = "".join(code_element.itertext()).strip()
        if not value:
          continue
        if local_paragraph.xpath(
            ".//code[normalize-space(string())=$value]", value=value):
          continue
        source_element = code_element
        if code_element.getparent().tag == "a":
          source_element = code_element.getparent()
          source_href = source_element.get("href", "")
          if source_href and not source_href.startswith(("http://", "https://")):
            source_element.set("href", urljoin(official_page_url, source_href))
        markup = etree.tostring(
          source_element, encoding="unicode", method="html", with_tail=False
        )
        _wrap_text_occurrence(local_paragraph, value, markup)


# ===== Apply reviewed prose corrections ===================================== #
def _apply_prose_corrections(tree, page_path):
  if page_path.name != "launch_app.html":
    return
  sections = tree.xpath("//section[@id='deep-dive-into-applauncher']")
  if not sections:
    return
  paragraphs = sections[0].xpath("./p")
  if len(paragraphs) < 2:
    return

  app_launcher = _api_link(APP_LAUNCHER_LINK, "app.AppLauncher")
  simulation_app = _api_link(
    SIMULATION_APP_LINK, "isaacsim.simulation_app.SimulationApp"
  )
  extension = '<span class="term">Extension</span>'
  cli = '<span class="term">CLI</span>'

  introductions = (
    (
      f"本教程将深入介绍如何使用 {app_launcher}，通过 {cli} 参数和环境变量"
      f"配置 Simulator。重点演示如何启用实时串流、配置 {app_launcher} 所封装的"
      f" {simulation_app} 实例，同时兼容用户自定义选项。"
    ),
    (
      f"{app_launcher} 对 {simulation_app} 进行了封装，目的是简化后者的配置。"
      f"{simulation_app} 需要加载多个 {extension} 才能启用相应功能；其中部分 "
      f"{extension} 对加载顺序有明确要求，并且彼此存在依赖关系。"
    ),
    (
      f"此外，<code>headless</code> 等启动选项必须在创建实例时确定，并可能与特定 "
      f"{extension} 存在隐式关联，例如实时串流相关的 {extension}。"
      f"{app_launcher} 为这些 {extension} 和启动选项提供了统一、可移植的配置接口，"
      f"适用于不同的使用场景。为此，它提供了可与用户自定义参数合并的 {cli} "
      f"及环境变量选项，并将属于 {simulation_app} 的参数继续传递给该实例。"
      f"该启动工具由 <code>isaaclab.app</code> Module 提供。"
    ),
  )
  for paragraph, introduction in zip(paragraphs[:2], introductions[:2]):
    _replace_paragraph(paragraph, introduction)
  current_paragraphs = sections[0].xpath("./p")
  third_paragraph = html.fragment_fromstring(
    f"<p>{introductions[2]}</p>"
  )
  if len(current_paragraphs) >= 3:
    current_paragraphs[2].getparent().replace(
      current_paragraphs[2], third_paragraph
    )
  else:
    current_paragraphs[1].addnext(third_paragraph)


# ===== Remove an existing number span ======================================= #
def _remove_existing_number(heading):
  for number_span in heading.xpath(
      "./span[contains(concat(' ', normalize-space(@class), ' '), "
      "' heading-number ')]"):
    number_span.drop_tree()


# ===== Set one heading number =============================================== #
def _set_heading_number(heading, number):
  _remove_existing_number(heading)
  original_text = heading.text or ""
  heading.text = None
  number_span = etree.Element("span")
  number_span.set("class", "heading-number")
  number_span.text = number
  number_span.tail = " " + original_text.lstrip()
  heading.insert(0, number_span)


# ===== Ensure a heading anchor ============================================== #
def _ensure_heading_id(heading):
  parent = heading.getparent()
  if heading.get("id"):
    if parent is not None and parent.get("id") == heading.get("id"):
      del parent.attrib["id"]
    return
  if parent is not None and parent.get("id"):
    heading.set("id", parent.get("id"))
    del parent.attrib["id"]


# ===== Number all headings on one page ====================================== #
def _number_page_headings(main_content):
  page_titles = main_content.xpath(".//h1")
  if not page_titles:
    return
  for duplicate_title in page_titles[1:]:
    duplicate_title.drop_tree()
  _remove_existing_number(page_titles[0])

  level_two_index = 0
  level_three_index = 0
  level_four_index = 0
  for heading in main_content.xpath(".//h2 | .//h3 | .//h4"):
    _ensure_heading_id(heading)
    if heading.tag == "h2":
      level_two_index += 1
      level_three_index = 0
      level_four_index = 0
      number = f"{level_two_index}"
    elif heading.tag == "h3":
      level_three_index += 1
      level_four_index = 0
      number = f"{level_two_index}.{level_three_index}"
    else:
      level_four_index += 1
      number = (
        f"{level_two_index}.{level_three_index}.{level_four_index}"
      )
    _set_heading_number(heading, number)


# ===== Synchronize the page table of contents =============================== #
def _synchronize_toc(tree):
  toc_elements = tree.xpath("//aside[contains(@class, 'toc')]")
  if not toc_elements:
    return
  toc = toc_elements[0]
  for link in toc.xpath("./a"):
    link.drop_tree()
  for heading in tree.xpath(
      "//main[contains(@class, 'content')]//h2 | "
      "//main[contains(@class, 'content')]//h3 | "
      "//main[contains(@class, 'content')]//h4"):
    if not heading.get("id"):
      continue
    link = etree.Element("a")
    link.set("href", "#" + heading.get("id"))
    if heading.tag == "h3":
      link.set("class", "toc-level-2")
    elif heading.tag == "h4":
      link.set("class", "toc-level-3")
    link.text = " ".join(heading.text_content().split())
    toc.append(link)


# ===== Normalize one HTML page ============================================== #
def _normalize_page(page_path):
  tree = html.parse(str(page_path))
  _apply_prose_corrections(tree, page_path)
  _apply_reviewed_introductions(tree, page_path)
  _apply_recurring_prose_fixes(tree)
  _correct_source_location_paragraphs(tree)
  _correct_isolated_paragraphs(tree, page_path)
  _apply_heading_corrections(tree)
  _apply_reviewed_section_prose(tree, page_path)
  _restore_inline_code(tree, page_path)
  for translation_badge in tree.xpath(
      "//*[contains(concat(' ', normalize-space(@class), ' '), "
      "' translation-badge ')]"):
    translation_badge.drop_tree()
  main_contents = tree.xpath("//main[contains(@class, 'content')]")
  if not main_contents:
    return
  _number_page_headings(main_contents[0])
  _synchronize_toc(tree)
  document = "<!doctype html>\n" + etree.tostring(
    tree.getroot(), encoding="unicode", method="html"
  )
  page_path.write_text(document, encoding="utf-8")


# ===== Normalize every documentation page ================================== #
def main():
  """Normalize headings in every generated HTML documentation page."""
  for page_path in DOCUMENT_ROOT.rglob("*.html"):
    _normalize_page(page_path)


if __name__ == "__main__":
  main()
