"""批量保存单环境 physics-rate 飞行状态与物理控制量。"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import TextIO

import torch

from .flight_plotter import show_flight_csv
from .flight_schema import CSV_COLUMNS, FLIGHT_SAMPLE_WIDTH


class FlightLogger:
  """把一个 environment 的 physics-rate 飞行数据写入 CSV。"""

  # ===== __init__ =========================================================== #
  def __init__(self, output_root: str | Path, env_id: int,
               flush_interval: int, plot: bool) -> None:
    """创建本次运行的时间戳输出目录和 CSV 文件。

    Args:
      output_root: 所有飞行日志运行目录的共同根目录。
      env_id: 写入 CSV 的 environment 标识。
      flush_interval: 每写入多少行刷新一次 CSV。
      plot: 关闭 Logger 后是否直接显示分类曲线 Figure。

    Raises:
      ValueError: 环境索引为负数或刷新间隔不是正数。
    """
    if env_id < 0:
      raise ValueError("env_id must be non-negative.")
    if flush_interval < 1:
      raise ValueError("flush_interval must be positive.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    self._run_directory = Path(output_root).expanduser().resolve() / timestamp
    self._run_directory.mkdir(parents=True, exist_ok=False)
    self._csv_path = self._run_directory / "flight.csv"
    self._env_id = env_id
    self._flush_interval = flush_interval
    self._plot = plot
    self._row_count = 0
    self._closed = False
    self._csv_file: TextIO = self._csv_path.open(
      "w", encoding="utf-8", newline=""
    )
    self._writer = csv.DictWriter(self._csv_file, fieldnames=CSV_COLUMNS)
    self._writer.writeheader()

  # ===== run_directory ====================================================== #
  @property
  def run_directory(self) -> Path:
    """返回当前运行的日志目录。"""
    return self._run_directory

  # ===== csv_path =========================================================== #
  @property
  def csv_path(self) -> Path:
    """返回当前运行的 CSV 路径。"""
    return self._csv_path

  # ===== log_batch ========================================================== #
  def log_batch(self, samples: torch.Tensor) -> None:
    """批量写入连续的 physics-rate 飞行数据。

    Args:
      samples: 形状为 ``(num_samples, FLIGHT_SAMPLE_WIDTH)`` 的 tensor；
        第一列为仿真时间，其余列顺序由固定 CSV schema 定义。

    Raises:
      RuntimeError: Logger 已关闭。
      ValueError: 输入 tensor 形状或仿真时间不符合接口约定。
    """
    if self._closed:
      raise RuntimeError("Cannot write to a closed FlightLogger.")
    if samples.ndim != 2 or samples.shape[1] != FLIGHT_SAMPLE_WIDTH:
      raise ValueError("samples has an invalid shape.")
    if samples.shape[0] == 0:
      return

    cpu_rows = samples.detach().to(
      device="cpu", dtype=torch.float64
    ).tolist()
    if any(sample[0] < 0.0 for sample in cpu_rows):
      raise ValueError("simulation_time_s must be non-negative.")
    for sample in cpu_rows:
      row_values = (sample[0], self._env_id, *sample[1:])
      self._writer.writerow(dict(zip(CSV_COLUMNS, row_values, strict=True)))
    previous_row_count = self._row_count
    self._row_count += len(cpu_rows)
    previous_flush_count = previous_row_count // self._flush_interval
    current_flush_count = self._row_count // self._flush_interval
    if current_flush_count > previous_flush_count:
      self._csv_file.flush()

  # ===== close ============================================================== #
  def close(self) -> None:
    """刷新并关闭 CSV，然后按配置显示飞行曲线 Figure。"""
    if self._closed:
      return
    self._csv_file.flush()
    self._csv_file.close()
    self._closed = True
    if self._plot and self._row_count > 0:
      show_flight_csv(self._csv_path)
