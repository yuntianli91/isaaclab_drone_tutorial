# Configurations

本目录保存可直接序列化、需要随实验调整的具体配置值。Python `Cfg` 类继续
负责类型约束、`class_type`、Manager 函数以及对象组合关系。

```text
configs/
├── common/
│   └── uav_obstacle_base.yaml
├── tasks/
│   └── hover_fixed.yaml
└── tutorials/
    └── tutorial1.yaml
```

YAML 是各 Tutorial 运行参数的唯一来源。入口命令行只接收可选的
`--config PATH`，用于选择配置文件。YAML 中的 `null` 会被加载为 Python
`None`，用于明确表示该参数尚未确认。

`common/` 保存 UAV、场景、仿真周期和内层飞控等稳定配置；`tasks/` 保存
observation、action、reset 和目标等任务语义；`tutorials/` 保存各入口的运行
参数、飞行日志参数和覆盖值。每个 Tutorial 使用独立的顶层 YAML，例如后续可
增加 `tutorial2.yaml`。

顶层配置通过 `base` 按顺序继承其他 YAML。mapping 会递归合并，scalar 和
list 会整项覆盖；相对路径以声明它的 YAML 所在目录为基准。例如：

```yaml
# 依次加载的稳定公共配置。
base:
  - ../common/uav_obstacle_base.yaml  # UAV 和场景配置。
  - ../tasks/hover_fixed.yaml         # 固定悬停任务配置。
```

`src/isaaclab_uav_tutorial/config/yaml_loader.py` 提供公共 YAML 读取和基础
类型检查；各 Tutorial 只需定义自己的参数模型与装配逻辑。
