"""FlightLogger 的固定 CSV 字段定义。"""

FLIGHT_SAMPLE_COLUMNS = (
  "simulation_time_s",
  "state/position_e_x_m",
  "state/position_e_y_m",
  "state/position_e_z_m",
  "state/quaternion_eb_w",
  "state/quaternion_eb_x",
  "state/quaternion_eb_y",
  "state/quaternion_eb_z",
  "state/linear_velocity_e_x_mps",
  "state/linear_velocity_e_y_mps",
  "state/linear_velocity_e_z_mps",
  "state/angular_velocity_b_x_radps",
  "state/angular_velocity_b_y_radps",
  "state/angular_velocity_b_z_radps",
  "command/desired_velocity_e_x_mps",
  "command/desired_velocity_e_y_mps",
  "command/desired_velocity_e_z_mps",
  "command/desired_yaw_e_rad",
  "control/collective_thrust_n",
  "control/desired_quaternion_eb_w",
  "control/desired_quaternion_eb_x",
  "control/desired_quaternion_eb_y",
  "control/desired_quaternion_eb_z",
  "control/body_torque_b_x_nm",
  "control/body_torque_b_y_nm",
  "control/body_torque_b_z_nm",
)

CSV_COLUMNS = (
  FLIGHT_SAMPLE_COLUMNS[0],
  "env_id",
  *FLIGHT_SAMPLE_COLUMNS[1:],
)

FLIGHT_SAMPLE_WIDTH = len(FLIGHT_SAMPLE_COLUMNS)
