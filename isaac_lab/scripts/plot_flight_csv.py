"""直接读取 FlightLogger CSV 并显示飞行数据 Figure。"""

from __future__ import annotations

import argparse
from pathlib import Path

from isaaclab_uav_tutorial.monitoring import show_flight_csv


# ===== main ================================================================= #
def main() -> None:
  """解析 CSV 路径并启动独立的 Matplotlib 绘图窗口。"""
  parser = argparse.ArgumentParser(
    description="Plot a FlightLogger CSV without starting Isaac Sim."
  )
  parser.add_argument("csv_path", type=Path,
                      help="Path to a FlightLogger flight.csv file.")
  args = parser.parse_args()
  csv_path = args.csv_path.expanduser().resolve()
  if not csv_path.is_file():
    parser.error(f"CSV file does not exist: {csv_path}")

  try:
    show_flight_csv(csv_path)
  except (KeyError, OSError, TypeError, ValueError) as error:
    parser.error(f"failed to plot CSV: {error}")


if __name__ == "__main__":
  main()
