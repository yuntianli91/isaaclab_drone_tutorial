# Tests

Tutorial 0 的验收依赖 Isaac Sim 进程和 GPU，当前通过记录在
`docs/progress.md` 中的 smoke commands 验证，不放入普通 CPU pytest。

`test_flight_logger.py` 使用 CPU tensor 验证 physics-rate 批量 CSV 写入且不会
生成 PNG。`test_physics_step_flight_buffer.py` 验证完整的 `W → E` 位置、自由
向量和姿态变换。Tutorial 1 的 Manager、reset、batch shape 和 finite value
仍通过 Isaac Sim smoke test 验证。
