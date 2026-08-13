"""FlightLogger 的 CPU 单元测试。"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import torch
from matplotlib import pyplot as plt

from isaaclab_uav_tutorial.monitoring import FlightLogger
from isaaclab_uav_tutorial.monitoring.flight_plotter import show_flight_csv
from isaaclab_uav_tutorial.monitoring.flight_schema import FLIGHT_SAMPLE_WIDTH


# ===== test_flight_logger_writes_physics_samples ============================ #
def test_flight_logger_writes_physics_samples(tmp_path: Path) -> None:
  """验证 Logger 批量写入 physics samples 且不生成图片文件。"""
  samples = torch.zeros(2, FLIGHT_SAMPLE_WIDTH)
  samples[:, 0] = torch.tensor((0.0, 0.01))
  samples[:, 4] = 1.0
  samples[:, 19] = 1.0
  samples[1, 1:4] = torch.tensor((1.0, 2.0, 3.0))
  samples[1, 17] = 0.4

  logger = FlightLogger(output_root=tmp_path, env_id=1, flush_interval=1,
                        plot=False)
  logger.log_batch(samples)
  logger.close()

  with logger.csv_path.open(encoding="utf-8", newline="") as csv_file:
    rows = list(csv.DictReader(csv_file))
  assert len(rows) == 2
  assert len(rows[0]) == 27
  assert float(rows[1]["state/position_e_x_m"]) == 1.0
  desired_yaw = float(rows[1]["command/desired_yaw_e_rad"])
  assert math.isclose(desired_yaw, 0.4, rel_tol=1.0e-6)
  assert "control_step" not in rows[0]
  assert list(logger.run_directory.glob("*.png")) == []


# ===== test_flight_plotter_uses_one_axis_specific_figure ==================== #
def test_flight_plotter_uses_one_axis_specific_figure(
  tmp_path: Path, monkeypatch: object
) -> None:
  """验证全部物理量位于同一 Figure 且四元数和合力不直接绘制。"""
  samples = torch.zeros(2, FLIGHT_SAMPLE_WIDTH)
  samples[:, 0] = torch.tensor((0.0, 0.01))
  samples[:, 4] = 1.0
  samples[:, 19] = 1.0
  logger = FlightLogger(output_root=tmp_path, env_id=0, flush_interval=1,
                        plot=False)
  logger.log_batch(samples)
  logger.close()

  show_calls = []
  monkeypatch.setattr(plt, "show", lambda: show_calls.append(True))
  show_flight_csv(logger.csv_path)

  figures = [plt.figure(number) for number in plt.get_fignums()]
  assert len(figures) == 1
  assert len(figures[0].axes) == 16
  assert show_calls == [True]
  assert all("quaternion" not in axis.get_title().lower()
             for figure in figures for axis in figure.axes)
  assert all("body force" not in axis.get_title().lower()
             for figure in figures for axis in figure.axes)
  titles = [axis.get_title() for axis in figures[0].axes]
  expected_titles = [
    r"$p_{x}^E$",
    r"$v_{x}^E$",
    r"$p_{y}^E$",
    r"$v_{y}^E$",
    r"$p_{z}^E$",
    r"$v_{z}^E$",
    r"$\phi_{EB}$",
    r"$\omega_{x}^B$",
    r"$\theta_{EB}$",
    r"$\omega_{y}^B$",
    r"$\psi_{EB}$",
    r"$\omega_{z}^B$",
    r"$T$",
    r"$\tau_{x}^B$",
    r"$\tau_{y}^B$",
    r"$\tau_{z}^B$",
  ]
  assert titles == expected_titles
  for axis in figures[0].axes:
    assert all(line.get_linewidth() == 2.0 for line in axis.lines)
    assert axis.get_legend()._loc == 1
  plt.close("all")
