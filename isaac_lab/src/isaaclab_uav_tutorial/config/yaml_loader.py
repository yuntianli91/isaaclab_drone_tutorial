"""可供后续 Tutorial 复用的 YAML 加载与基本类型检查。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml


# ===== _read_yaml_mapping =================================================== #
def _read_yaml_mapping(config_path: Path) -> Mapping[str, Any]:
  """读取单个以 mapping 为根节点的 YAML 文件。"""
  with config_path.open(encoding="utf-8") as config_file:
    raw_data = yaml.safe_load(config_file)
  if not isinstance(raw_data, Mapping):
    raise ValueError(f"The YAML root in {config_path} must be a mapping.")
  return raw_data


# ===== _merge_mappings ====================================================== #
def _merge_mappings(base: Mapping[str, Any],
                    override: Mapping[str, Any]) -> dict[str, Any]:
  """递归合并 mapping，并让后加载的值覆盖先加载的值。"""
  merged = dict(base)
  for key, override_value in override.items():
    base_value = merged.get(key)
    if isinstance(base_value, Mapping) and isinstance(override_value, Mapping):
      merged[key] = _merge_mappings(base_value, override_value)
    else:
      merged[key] = override_value
  return merged


# ===== _load_yaml_mapping_recursive ========================================= #
def _load_yaml_mapping_recursive(config_path: Path,
                                 active_paths: tuple[Path, ...]
                                 ) -> dict[str, Any]:
  """递归加载一个 YAML 及其 ``base`` 配置。"""
  if config_path in active_paths:
    cycle = " -> ".join(str(path) for path in (*active_paths, config_path))
    raise ValueError(f"YAML base cycle detected: {cycle}")

  raw_data = _read_yaml_mapping(config_path)
  base_entries = raw_data.get("base", [])
  invalid_base = isinstance(base_entries, (str, bytes))
  invalid_base = invalid_base or not isinstance(base_entries, Sequence)
  if invalid_base:
    raise ValueError(f"{config_path}: base must be a sequence of paths.")

  merged: dict[str, Any] = {}
  next_active_paths = (*active_paths, config_path)
  for base_entry in base_entries:
    if not isinstance(base_entry, str) or not base_entry:
      raise ValueError(f"{config_path}: every base path must be a string.")
    base_path = (config_path.parent / base_entry).expanduser().resolve()
    base_data = _load_yaml_mapping_recursive(base_path, next_active_paths)
    merged = _merge_mappings(merged, base_data)

  local_data = {key: value for key, value in raw_data.items() if key != "base"}
  return _merge_mappings(merged, local_data)


# ===== load_yaml_mapping ==================================================== #
def load_yaml_mapping(config_path: str | Path) -> Mapping[str, Any]:
  """读取 YAML 文件并递归合并其 ``base`` 配置。

  Args:
    config_path: 顶层 YAML 配置文件路径。相对 ``base`` 路径以声明它的
      YAML 文件所在目录为基准。

  Returns:
    不包含 ``base`` 元数据的合并后根 mapping。

  Raises:
    FileNotFoundError: 配置文件不存在。
    ValueError: YAML 结构、``base`` 路径或继承关系无效。
  """
  path = Path(config_path).expanduser().resolve()
  return _load_yaml_mapping_recursive(path, ())


# ===== reject_unknown_keys ================================================== #
def reject_unknown_keys(data: Mapping[str, Any], allowed_keys: Sequence[str],
                        location: str) -> None:
  """拒绝配置 mapping 中没有定义的字段。

  Args:
    data: 需要检查的配置 mapping。
    allowed_keys: 当前 mapping 支持的字段名称。
    location: 用于错误信息的配置位置。

  Raises:
    ValueError: mapping 中存在未知字段。
  """
  allowed_key_set = set(allowed_keys)
  unknown_keys = sorted(str(key) for key in data if key not in allowed_key_set)
  if unknown_keys:
    raise ValueError(f"{location} contains unknown fields: {unknown_keys}")


# ===== require_mapping ====================================================== #
def require_mapping(data: Mapping[str, Any], key: str,
                    location: str) -> Mapping[str, Any]:
  """读取必需的 YAML mapping。"""
  value = data.get(key)
  if not isinstance(value, Mapping):
    raise ValueError(f"{location}.{key} must be a mapping.")
  return value


# ===== require_string ======================================================= #
def require_string(data: Mapping[str, Any], key: str,
                   location: str) -> str:
  """读取非空字符串参数。"""
  value = data.get(key)
  if not isinstance(value, str) or not value:
    raise ValueError(f"{location}.{key} must be a non-empty string.")
  return value


# ===== require_bool ========================================================= #
def require_bool(data: Mapping[str, Any], key: str,
                 location: str) -> bool:
  """读取布尔参数。"""
  value = data.get(key)
  if not isinstance(value, bool):
    raise ValueError(f"{location}.{key} must be a boolean.")
  return value


# ===== require_int ========================================================== #
def require_int(data: Mapping[str, Any], key: str,
                location: str) -> int:
  """读取整数参数，同时拒绝布尔值。"""
  value = data.get(key)
  if isinstance(value, bool) or not isinstance(value, int):
    raise ValueError(f"{location}.{key} must be an integer.")
  return value


# ===== require_float ======================================================== #
def require_float(data: Mapping[str, Any], key: str,
                  location: str) -> float:
  """读取浮点参数，同时拒绝布尔值。"""
  value = data.get(key)
  if isinstance(value, bool) or not isinstance(value, (int, float)):
    raise ValueError(f"{location}.{key} must be a number.")
  return float(value)


# ===== require_float_tuple ================================================== #
def require_float_tuple(data: Mapping[str, Any], key: str,
                        location: str, length: int) -> tuple[float, ...]:
  """读取指定长度的浮点序列。"""
  value = data.get(key)
  if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
    raise ValueError(f"{location}.{key} must contain exactly {length} "
                     "numbers.")
  invalid_item = any(isinstance(item, bool)
                     or not isinstance(item, (int, float)) for item in value)
  if len(value) != length or invalid_item:
    raise ValueError(f"{location}.{key} must contain exactly {length} "
                     "numbers.")
  return tuple(float(item) for item in value)


# ===== require_range_mapping ================================================ #
def require_range_mapping(data: Mapping[str, Any], key: str, location: str,
                          range_keys: Sequence[str]
                          ) -> dict[str, tuple[float, float]]:
  """读取由若干 ``[lower, upper]`` 组成的范围 mapping。"""
  ranges = require_mapping(data, key, location)
  result: dict[str, tuple[float, float]] = {}
  range_location = f"{location}.{key}"
  reject_unknown_keys(ranges, range_keys, range_location)
  for range_key in range_keys:
    lower, upper = require_float_tuple(ranges, range_key, range_location,
                                       length=2)
    if lower > upper:
      raise ValueError(f"{range_location}.{range_key} lower bound exceeds "
                       "upper bound.")
    result[range_key] = (lower, upper)
  return result
