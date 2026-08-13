"""从 FlightLogger CSV 生成分类飞行曲线。"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.axes import Axes

LINE_WIDTH = 2.0


# ===== _read_csv_columns ==================================================== #
def _read_csv_columns(csv_path: Path) -> dict[str, list[float]]:
  """把 CSV 中的每个字段读取成独立浮点序列。"""
  with csv_path.open(encoding="utf-8", newline="") as csv_file:
    reader = csv.DictReader(csv_file)
    if reader.fieldnames is None:
      raise ValueError(f"CSV has no header: {csv_path}")
    columns = {field_name: [] for field_name in reader.fieldnames}
    for row in reader:
      for field_name in reader.fieldnames:
        columns[field_name].append(float(row[field_name]))
  if not columns or not next(iter(columns.values())):
    raise ValueError(f"CSV has no flight samples: {csv_path}")
  return columns


# ===== _quaternion_to_euler ================================================= #
def _quaternion_to_euler(w_values: list[float], x_values: list[float],
                         y_values: list[float], z_values: list[float]
                         ) -> tuple[list[float], list[float], list[float]]:
  """把 WXYZ 四元数序列转换成 XYZ Euler 角 (rad)。"""
  roll_values = []
  pitch_values = []
  yaw_values = []
  quaternions = zip(w_values, x_values, y_values, z_values, strict=True)
  for w_value, x_value, y_value, z_value in quaternions:
    roll_sine = 2.0 * (w_value * x_value + y_value * z_value)
    roll_cosine = 1.0 - 2.0 * (x_value**2 + y_value**2)
    roll_values.append(math.atan2(roll_sine, roll_cosine))

    pitch_sine = 2.0 * (w_value * y_value - z_value * x_value)
    pitch_sine = min(1.0, max(-1.0, pitch_sine))
    pitch_values.append(math.asin(pitch_sine))

    yaw_sine = 2.0 * (w_value * z_value + x_value * y_value)
    yaw_cosine = 1.0 - 2.0 * (y_value**2 + z_value**2)
    yaw_values.append(math.atan2(yaw_sine, yaw_cosine))
  return roll_values, pitch_values, yaw_values


# ===== _plot_columns ======================================================== #
def _plot_columns(axis: Axes, time_values: list[float],
                  columns: dict[str, list[float]], field_names: tuple[str, ...],
                  labels: tuple[str, ...], title: str, unit: str) -> None:
  """在单轴 subplot 中绘制 actual、desired 或控制输出。"""
  for field_name, label in zip(field_names, labels, strict=True):
    axis.plot(time_values, columns[field_name], label=label,
              linewidth=LINE_WIDTH)
  axis.set_title(title)
  axis.set_xlabel("Simulation time (s)")
  axis.set_ylabel(unit)
  axis.grid(True, alpha=0.3)
  axis.legend(loc="upper right")


# ===== show_flight_csv ====================================================== #
def show_flight_csv(csv_path: str | Path) -> None:
  """读取飞行 CSV 并直接显示包含全部数据的分类曲线窗口。

  Args:
    csv_path: FlightLogger 生成的 CSV 路径。

  Raises:
    ValueError: CSV 缺少表头或飞行数据。
  """
  csv_file_path = Path(csv_path).expanduser().resolve()
  columns = _read_csv_columns(csv_file_path)
  time_values = columns["simulation_time_s"]

  actual_euler = _quaternion_to_euler(
    columns["state/quaternion_eb_w"], columns["state/quaternion_eb_x"],
    columns["state/quaternion_eb_y"], columns["state/quaternion_eb_z"]
  )
  desired_euler = _quaternion_to_euler(
    columns["control/desired_quaternion_eb_w"],
    columns["control/desired_quaternion_eb_x"],
    columns["control/desired_quaternion_eb_y"],
    columns["control/desired_quaternion_eb_z"]
  )
  columns["derived/roll_rad"] = actual_euler[0]
  columns["derived/pitch_rad"] = actual_euler[1]
  columns["derived/yaw_rad"] = actual_euler[2]
  columns["derived/desired_roll_rad"] = desired_euler[0]
  columns["derived/desired_pitch_rad"] = desired_euler[1]
  columns["derived/desired_yaw_rad"] = desired_euler[2]

  position_fields = (
    "state/position_e_x_m",
    "state/position_e_y_m",
    "state/position_e_z_m",
  )
  actual_velocity_fields = (
    "state/linear_velocity_e_x_mps",
    "state/linear_velocity_e_y_mps",
    "state/linear_velocity_e_z_mps",
  )
  desired_velocity_fields = (
    "command/desired_velocity_e_x_mps",
    "command/desired_velocity_e_y_mps",
    "command/desired_velocity_e_z_mps",
  )
  actual_attitude_fields = (
    "derived/roll_rad",
    "derived/pitch_rad",
    "derived/yaw_rad",
  )
  desired_attitude_fields = (
    "derived/desired_roll_rad",
    "derived/desired_pitch_rad",
    "derived/desired_yaw_rad",
  )
  angular_velocity_fields = (
    "state/angular_velocity_b_x_radps",
    "state/angular_velocity_b_y_radps",
    "state/angular_velocity_b_z_radps",
  )
  body_torque_fields = (
    "control/body_torque_b_x_nm",
    "control/body_torque_b_y_nm",
    "control/body_torque_b_z_nm",
  )

  figure, axes = plt.subplots(
    9, 2, figsize=(18.0, 28.0), sharex=True, constrained_layout=True
  )
  figure.suptitle("UAV Flight Data", fontsize=16)
  figure.canvas.manager.set_window_title("FlightLogger")
  axis_symbols = ("x", "y", "z")
  attitude_symbols = (r"\phi", r"\theta", r"\psi")

  for axis_index in range(3):
    axis_symbol = axis_symbols[axis_index]
    _plot_columns(
      axes[axis_index, 0], time_values, columns,
      (position_fields[axis_index],), ("actual",),
      rf"$p_{{{axis_symbol}}}^E$", "m"
    )
    _plot_columns(
      axes[3 + axis_index, 0], time_values, columns,
      (actual_attitude_fields[axis_index],
       desired_attitude_fields[axis_index]),
      ("actual", "desired"),
      rf"${attitude_symbols[axis_index]}_{{EB}}$", "rad"
    )
    _plot_columns(
      axes[axis_index, 1], time_values, columns,
      (actual_velocity_fields[axis_index],
       desired_velocity_fields[axis_index]),
      ("actual", "desired"),
      rf"$v_{{{axis_symbol}}}^E$", "m/s"
    )
    _plot_columns(
      axes[3 + axis_index, 1], time_values, columns,
      (angular_velocity_fields[axis_index],), ("actual",),
      rf"$\omega_{{{axis_symbol}}}^B$", "rad/s"
    )
    _plot_columns(
      axes[6 + axis_index, 1], time_values, columns,
      (body_torque_fields[axis_index],), ("body torque",),
      rf"$\tau_{{{axis_symbol}}}^B$", "N·m"
    )

  _plot_columns(
    axes[6, 0], time_values, columns,
    ("control/collective_thrust_n",), ("collective thrust",),
    r"$T$", "N"
  )
  figure.delaxes(axes[7, 0])
  figure.delaxes(axes[8, 0])
  plt.show()
