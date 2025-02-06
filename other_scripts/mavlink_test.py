from pymavlink import mavutil
import time

print("Trying to connect...")
connection = mavutil.mavlink_connection("tcp:192.168.0.155:5762")

print("Requesting data streams...")
connection.mav.request_data_stream_send(
    connection.target_system,
    connection.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL,
    10,  # Frequency (Hz)
    1     # Enable
)

print("Sending heartbeat request...")
connection.mav.heartbeat_send(
    mavutil.mavlink.MAV_TYPE_GCS,  # Ground Control Station
    mavutil.mavlink.MAV_AUTOPILOT_INVALID,
    0,
    0,
    0
)

print("Waiting for heartbeat...")
while True:
    msg = connection.recv_match(type='HEARTBEAT', blocking=True, timeout=5)
    if msg:
        print(f"✅ Received heartbeat from system {msg.get_srcSystem()} component {msg.get_srcComponent()}")
        break
    else:
        print("❌ No heartbeat yet, retrying...")
