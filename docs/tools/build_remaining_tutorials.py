"""Build the remaining Isaac Lab v2.3.2 Chinese tutorial pages."""

import concurrent.futures
from html import escape as escape_html
import json
import os
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request

from lxml import etree, html


DOCUMENT_ROOT = Path(
  "/home/yuntian/gitRepos/isaac_tutorial/docs/isaaclab-v2.3.2-zh"
)
OFFICIAL_HTML_ROOT = Path("/tmp/isaaclab-v2.3.2-html")
TRANSLATION_CACHE_PATH = Path("/tmp/isaaclab-v2.3.2-translation-cache.json")
OFFICIAL_BASE_URL = "https://isaac-sim.github.io/IsaacLab/v2.3.2/"
TRANSLATION_URL = "https://translate.googleapis.com/translate_a/single"

PAGES = (
  ("00_sim/spawn_prims", "在 Scene 中生成 Prim"),
  ("00_sim/launch_app", "深入了解 AppLauncher"),
  ("01_assets/add_new_robot", "向 Isaac Lab 添加新 Robot"),
  ("01_assets/run_rigid_object", "与 Rigid Object 交互"),
  ("01_assets/run_articulation", "与 Articulation 交互"),
  ("01_assets/run_deformable_object", "与 Deformable Object 交互"),
  ("01_assets/run_surface_gripper", "与 Surface Gripper 交互"),
  ("02_scene/create_scene", "使用 Interactive Scene"),
  ("03_envs/create_manager_base_env", "创建 Manager-Based Base Environment"),
  ("03_envs/create_manager_rl_env", "创建 Manager-Based RL Environment"),
  ("03_envs/create_direct_rl_env", "创建 Direct Workflow RL Environment"),
  ("03_envs/register_rl_env_gym", "注册 Environment"),
  ("03_envs/run_rl_training", "使用 RL Agent 训练"),
  ("03_envs/configuring_rl_training", "配置 RL Agent"),
  ("03_envs/modify_direct_rl_env", "修改现有 Direct RL Environment"),
  ("03_envs/policy_inference_in_usd", "USD Environment 中的 Policy Inference"),
  ("04_sensors/add_sensors_on_robot", "在 Robot 上添加 Sensors"),
  ("05_controllers/run_diff_ik", "使用 Task-Space Controller"),
  ("05_controllers/run_osc", "使用 Operational Space Controller"),
)

GROUPS = (
  ("设置简单仿真", ("00_sim/create_empty", "00_sim/spawn_prims",
                  "00_sim/launch_app")),
  ("与 Assets 交互", ("01_assets/add_new_robot",
                      "01_assets/run_rigid_object",
                      "01_assets/run_articulation",
                      "01_assets/run_deformable_object",
                      "01_assets/run_surface_gripper")),
  ("创建 Scene", ("02_scene/create_scene",)),
  ("设计 Environment", ("03_envs/create_manager_base_env",
                         "03_envs/create_manager_rl_env",
                         "03_envs/create_direct_rl_env",
                         "03_envs/register_rl_env_gym",
                         "03_envs/run_rl_training",
                         "03_envs/configuring_rl_training",
                         "03_envs/modify_direct_rl_env",
                         "03_envs/policy_inference_in_usd")),
  ("集成 Sensors", ("04_sensors/add_sensors_on_robot",)),
  ("使用 Motion Generators", ("05_controllers/run_diff_ik",
                              "05_controllers/run_osc")),
)

PAGE_TITLES = dict(PAGES)
PAGE_TITLES["00_sim/create_empty"] = "创建空场景"

TERMS = (
  "Isaac Lab Mimic", "Isaac Lab", "Isaac Sim", "NVIDIA PhysX",
  "Operational Space Controller", "Task-Space Controller",
  "Manager-Based RL Environment", "Manager-Based Base Environment",
  "Direct Workflow RL Environment", "Reinforcement Learning",
  "Simulation Context", "Simulation Application", "Simulation Environment",
  "Interactive Scene", "Deformable Object", "Rigid Object Collection",
  "Rigid Object", "Surface Gripper", "Off-Screen Rendering",
  "Command-Line Arguments", "Command-Line Options", "Motion Generator",
  "Motion Generators", "Inverse Kinematics", "Policy Inference",
  "Physics Handles", "Physics Handle", "Physics Scene", "Physics Engine",
  "Simulation Loop", "Simulation Step", "Simulation Steps",
  "Simulated Scene", "Simulated Object", "Simulated Objects",
  "Observation Space", "Action Space", "Reward Function",
  "Termination Condition", "Event Term", "Curriculum Term",
  "Environment Configuration", "Environment Configurations",
  "Scene Configuration", "Asset Configuration", "Sensor Configuration",
  "Configuration Class", "Configuration Classes", "Configuration Object",
  "Standalone Python Script", "Standalone Script", "Python Script",
  "Python Module", "Python Modules", "Source Code", "Use Case",
  "Task Space", "Joint Space", "Joint-Level", "Task-Level",
  "Domain Randomization", "Frame Transformer", "Contact Sensor",
  "Ray Caster", "Differential IK", "Jacobian Matrix", "Policy Network",
  "Neural Network", "State Machine", "Finite State Machine",
  "Gymnasium Environment", "Vectorized Environment", "Environment Wrapper",
  "RL Agent", "RL Library", "Manager-Based", "Direct Workflow",
  "AppLauncher", "SimulationContext", "SimulationCfg", "AssetBase",
  "RigidObject", "Articulation", "DeformableObject", "InteractiveScene",
  "ManagerBasedEnv", "ManagerBasedRLEnv", "DirectRLEnv", "SensorBase",
  "RayCaster", "FrameTransformer", "DifferentialIKController",
  "OperationalSpaceController", "Omniverse", "PhysX", "USD", "URDF",
  "MJCF", "API", "GPU", "CPU", "RL", "MDP", "FEM", "IK",
  "Simulator", "Simulation", "Rendering", "Renderer", "Render",
  "Timeline", "Headless", "Livestream", "Fabric", "Stage", "Scene",
  "Scenes", "Prim", "Prims", "Spawner", "Spawners", "Spawn", "Asset",
  "Assets", "Robot", "Robots", "Sensor", "Sensors", "Camera", "Cameras",
  "Environment", "Environments", "Agent", "Agents", "Policy", "Policies",
  "Action", "Actions", "Observation", "Observations", "Reward", "Rewards",
  "Termination", "Terminations", "Event", "Events", "Curriculum",
  "Controller", "Controllers", "Jacobian", "Articulation", "Articulations",
  "Tensor", "Tensors", "Buffer", "Buffers", "Device", "Devices",
  "Framework", "Repository", "Script", "Scripts", "Module", "Modules",
  "Class", "Classes", "Method", "Methods", "Object", "Objects",
  "Config", "Configs", "Configuration", "Configurations", "Parameter",
  "Parameters", "Workflow", "Workflows", "Wrapper", "Wrappers",
  "Backend", "Backends", "Environment Variable", "Environment Variables",
  "Argument", "Arguments", "Option", "Options", "Flag", "Flags",
  "Step", "Steps", "Reset", "Play", "Pause", "Terminal", "Extension",
  "Extensions", "Task", "Tasks", "Manager", "Managers", "Command",
  "Commands", "Term", "Terms", "Noise", "Gravity", "Quaternion",
  "Transform", "Transforms", "Pose", "Poses", "Velocity", "Velocities",
  "Position", "Positions", "Debug", "Debugging", "Visualization",
)

TERM_PATTERN = re.compile(
  r"(?<![A-Za-z])(" + "|".join(
    re.escape(term) for term in sorted(set(TERMS), key=len, reverse=True)
  ) + r")(?![A-Za-z])",
  re.IGNORECASE,
)
FILE_PATTERN = re.compile(
  r"(?<![\w/.-])([\w./-]+\.(?:py|yaml|yml|toml|usd|urdf|json))"
)
LOCAL_TERM_REPLACEMENTS = {
  "Universal Scene Description": "Universal Scene Description",
  "通用 Scene 描述": "Universal Scene Description",
  "有限元法": "Finite Element Method",
  "原始形状": "Primitive Shapes",
  "键值对": "Key-Value Pair",
  "状态机": "State Machine",
  "人际关系": "Relationships",
  "参与者": "Actor",
  "Pytorch": "PyTorch",
  "pytorch": "PyTorch",
  "jit": "JIT",
  "Github": "GitHub",
  "演员": "Actor",
  "评论家": "Critic",
  "剧集": "Episode",
  "episode": "Episode",
  "cartpole": "Cartpole",
  "重置": "Reset",
  "复位": "Reset",
  "基元": "Prim",
  "地平面": "Ground Plane",
  "时间线": "Timeline",
  "张量": "Tensor",
  "缓冲区": "Buffer",
  "刚体": "Rigid Body",
  "软体": "Soft Body",
  "碰撞": "Collision",
  "网格": "Mesh",
  "材质": "Material",
  "灯光": "Light",
  "节点": "Node",
  "函数": "Function",
  "color": "Color",
  "red": "Red",
}


# ===== Load translation cache =============================================== #
def _load_cache():
  if not TRANSLATION_CACHE_PATH.exists():
    return {}
  return json.loads(TRANSLATION_CACHE_PATH.read_text(encoding="utf-8"))


# ===== Save translation cache =============================================== #
def _save_cache(cache):
  TRANSLATION_CACHE_PATH.write_text(
    json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
  )


# ===== Mask protected terms ================================================= #
def _mask_terms(source, markers):
  def replace_term(match):
    canonical = next(
      term for term in TERMS if term.lower() == match.group(0).lower()
    )
    marker = f"ZXQTERM{len(markers):06d}QXZ"
    markers[marker] = canonical
    return marker

  def replace_file(match):
    marker = f"ZXQTERM{len(markers):06d}QXZ"
    markers[marker] = match.group(1)
    return marker

  masked = FILE_PATTERN.sub(replace_file, source)
  return TERM_PATTERN.sub(replace_term, masked)


# ===== Translate one text fragment ========================================== #
def _translate_fragment(source):
  request_data = urllib.parse.urlencode(
    {
      "client": "gtx",
      "sl": "en",
      "tl": "zh-CN",
      "dt": "t",
      "q": source,
    }
  ).encode("utf-8")
  request = urllib.request.Request(TRANSLATION_URL, data=request_data)
  for attempt in range(4):
    try:
      with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.loads(response.read().decode("utf-8"))
      return "".join(segment[0] for segment in payload[0] if segment[0])
    except Exception:
      if attempt == 3:
        raise
      time.sleep(2 ** attempt)
  return source


# ===== Translate document text nodes ======================================== #
def _translate_article(article, markers, cache):
  nodes = article.xpath(
    ".//text()[not(ancestor::pre) and not(ancestor::code) "
    "and not(ancestor::script) and not(ancestor::style) "
    "and not(ancestor::svg)]"
  )
  records = []
  pending = set()
  for node in nodes:
    stripped = str(node).strip()
    if not stripped or not re.search(r"[A-Za-z]", stripped):
      continue
    masked = _mask_terms(stripped, markers)
    leading = str(node)[:len(str(node)) - len(str(node).lstrip())]
    trailing = str(node)[len(str(node).rstrip()):]
    attribute = "text" if node.is_text else "tail"
    records.append((node.getparent(), attribute, leading, masked, trailing))
    if masked not in cache:
      pending.add(masked)

  if pending:
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
      translations = executor.map(_translate_fragment, sorted(pending))
      cache.update(zip(sorted(pending), translations))
    _save_cache(cache)

  for parent, attribute, leading, masked, trailing in records:
    translated = cache[masked]
    translated = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", translated)
    translated = translated.replace("代码为", "代码：")
    translated = translated.replace("守则", "代码")
    translated = translated.replace("注意力", "注意")
    for translated_term, canonical_term in LOCAL_TERM_REPLACEMENTS.items():
      if translated_term not in translated:
        continue
      marker = f"ZXQTERM{len(markers):06d}QXZ"
      markers[marker] = canonical_term
      if translated_term.isascii():
        translated = re.sub(
          rf"(?<![A-Za-z]){re.escape(translated_term)}(?![A-Za-z])",
          marker,
          translated,
        )
      else:
        translated = translated.replace(translated_term, marker)
    setattr(parent, attribute, leading + translated + trailing)


# ===== Normalize official article markup ==================================== #
def _normalize_article(article, page_key):
  for header_link in article.xpath(
      ".//*[contains(concat(' ', normalize-space(@class), ' '), "
      "' headerlink ')]"):
    header_link.drop_tree()

  for element in article.xpath(".//svg"):
    element.drop_tree()

  for details in article.xpath(".//details"):
    details.set("class", "code-details")
    summaries = details.xpath("./summary")
    if summaries:
      summary = summaries[0]
      text_parts = summary.xpath(
        ".//*[contains(@class, 'sd-summary-text')]//text()"
      )
      summary.clear()
      summary.text = "".join(text_parts).strip()

  for element in article.xpath(".//div"):
    classes = element.get("class", "").split()
    language = None
    if "highlight-python" in classes:
      language = "Python"
    elif "highlight-bash" in classes or "highlight-console" in classes:
      language = "Bash"
    if language:
      element.set("class", "code-block")
      element.set("data-language", language)

  for line_number in article.xpath(
      ".//*[contains(concat(' ', normalize-space(@class), ' '), "
      "' linenos ')]"):
    line_number.drop_tree()

  for image in article.xpath(".//img"):
    source = image.get("src", "")
    image.set("src", "../../assets/" + Path(source).name.replace(". ", "."))
    image.set("class", "tutorial-image")

  current_url = urllib.parse.urljoin(
    OFFICIAL_BASE_URL, f"source/tutorials/{page_key}.html"
  )
  page_lookup = {key: f"{key}.html" for key in PAGE_TITLES}
  for link in article.xpath(".//a[@href]"):
    target = link.get("href")
    if target.startswith("#"):
      continue
    absolute = urllib.parse.urljoin(current_url, target)
    match = re.search(r"/source/tutorials/(.+)\.html(#.*)?$", absolute)
    if match and match.group(1) in page_lookup:
      current_output = DOCUMENT_ROOT / "tutorials" / f"{page_key}.html"
      target_output = DOCUMENT_ROOT / "tutorials" / page_lookup[match.group(1)]
      relative = os.path.relpath(target_output, current_output.parent)
      link.set("href", relative + (match.group(2) or ""))
    else:
      link.set("href", absolute)

  for contents in article.xpath(
      ".//*[contains(concat(' ', normalize-space(@class), ' '), "
      "' contents ')]"):
    contents.drop_tree()

  for heading in article.xpath(".//h1"):
    heading.drop_tree()


# ===== Number article headings ============================================== #
def _number_headings(article):
  level_two_index = 0
  level_three_index = 0
  level_four_index = 0
  for heading in article.xpath(".//h2 | .//h3 | .//h4"):
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

    parent = heading.getparent()
    if heading.get("id"):
      if parent is not None and parent.get("id") == heading.get("id"):
        del parent.attrib["id"]
    elif parent is not None and parent.get("id"):
      heading.set("id", parent.get("id"))
      del parent.attrib["id"]

    original_text = heading.text or ""
    heading.text = None
    number_span = etree.Element("span")
    number_span.set("class", "heading-number")
    number_span.text = number
    number_span.tail = " " + original_text
    heading.insert(0, number_span)


# ===== Build shared sidebar ================================================= #
def _build_sidebar(page_key):
  parts = [
    '<a class="sidebar-root" data-search-item '
    'href="../../index.html">IsaacLab Tutorial</a>'
  ]
  for group_title, page_keys in GROUPS:
    parts.append(f'<div class="sidebar-title">{group_title}</div>')
    for target_key in page_keys:
      active = ' class="active"' if target_key == page_key else ""
      current_output = DOCUMENT_ROOT / "tutorials" / f"{page_key}.html"
      target_output = DOCUMENT_ROOT / "tutorials" / f"{target_key}.html"
      relative = os.path.relpath(target_output, current_output.parent)
      title = PAGE_TITLES[target_key]
      parts.append(
        f'<a{active} data-search-item href="{relative}">{title}</a>'
      )
  return "\n      ".join(parts)


# ===== Build page table of contents ========================================= #
def _build_toc(article):
  parts = ["<strong>本页目录</strong>"]
  for heading in article.xpath(".//h2 | .//h3"):
    heading_id = heading.get("id")
    if not heading_id:
      continue
    level_class = ' class="toc-level-2"' if heading.tag == "h3" else ""
    label = "".join(heading.itertext()).strip()
    parts.append(f'<a{level_class} href="#{heading_id}">{label}</a>')
  return "\n      ".join(parts)


# ===== Restore protected term markup ======================================== #
def _restore_terms(document, markers):
  for marker, term in markers.items():
    replacement = f'<span class="term">{escape_html(term)}</span>'
    document = document.replace(marker, replacement)
  return document


# ===== Render one translated page =========================================== #
def _render_page(page_key, title, previous_key, next_key, cache):
  source_path = OFFICIAL_HTML_ROOT / f"{page_key}.html"
  tree = html.parse(str(source_path))
  article = tree.xpath("//article[contains(@class, 'bd-article')]")[0]
  _normalize_article(article, page_key)
  markers = {}
  _translate_article(article, markers, cache)
  _number_headings(article)
  toc = _build_toc(article)
  article_markup = etree.tostring(article, encoding="unicode", method="html")
  sidebar = _build_sidebar(page_key)
  previous_title = PAGE_TITLES[previous_key]
  next_title = PAGE_TITLES[next_key]
  previous_href = os.path.relpath(
    DOCUMENT_ROOT / "tutorials" / f"{previous_key}.html",
    (DOCUMENT_ROOT / "tutorials" / f"{page_key}.html").parent,
  )
  next_href = os.path.relpath(
    DOCUMENT_ROOT / "tutorials" / f"{next_key}.html",
    (DOCUMENT_ROOT / "tutorials" / f"{page_key}.html").parent,
  )
  official_url = urllib.parse.urljoin(
    OFFICIAL_BASE_URL, f"source/tutorials/{page_key}.html"
  )
  document = f"""<!doctype html>
<html lang="zh-CN" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — Isaac Lab v2.3.2 中文文档</title>
  <link rel="stylesheet" href="../../assets/styles.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="../../index.html">
      <span class="brand-mark"></span>Isaac Lab 中文文档
    </a>
    <span class="version">v2.3.2</span>
    <input class="search" data-search type="search"
           placeholder="搜索教程目录……" aria-label="搜索教程目录">
    <button class="icon-button" data-theme-toggle type="button">明暗</button>
    <button class="icon-button menu-button" data-menu-toggle
            type="button">目录</button>
  </header>
  <div class="layout">
    <nav class="sidebar" aria-label="教程导航">
      {sidebar}
    </nav>
    <main class="content">
      <h1>{title}</h1>
      {article_markup}
      <nav class="page-nav" aria-label="翻页">
        <a href="{previous_href}">← 上一篇：{previous_title}</a>
        <a href="{next_href}">下一篇：{next_title} →</a>
      </nav>
      <footer class="page-footer">
        <p>原文：The Isaac Lab Project Developers。中文内容为非官方翻译；
        对应版本 v2.3.2。<a href="{official_url}">查看官方英文页面</a></p>
      </footer>
    </main>
    <aside class="toc" aria-label="本页目录">
      {toc}
    </aside>
  </div>
  <script src="../../assets/app.js"></script>
</body>
</html>
"""
  document = _restore_terms(document, markers)
  output_path = DOCUMENT_ROOT / "tutorials" / f"{page_key}.html"
  output_path.parent.mkdir(parents=True, exist_ok=True)
  output_path.write_text(document, encoding="utf-8")


# ===== Build all remaining pages ============================================ #
def main():
  """Build every remaining translated tutorial page."""
  cache = _load_cache()
  ordered_keys = ["00_sim/create_empty"] + [key for key, _ in PAGES]
  for page_key, title in PAGES:
    index = ordered_keys.index(page_key)
    previous_key = ordered_keys[index - 1]
    next_key = ordered_keys[(index + 1) % len(ordered_keys)]
    _render_page(page_key, title, previous_key, next_key, cache)


if __name__ == "__main__":
  main()
