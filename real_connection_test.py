from pymavlink import mavutil

# Replace "/dev/ttyACM0" with your actual Pixhawk device port
connection = mavutil.mavlink_connection('/dev/ttyACM0', baud=115200)

# Wait for a heartbeat from the Pixhawk
print("Waiting for heartbeat...")
connection.wait_heartbeat()
print(f"Heartbeat received from system {connection.target_system}, component {connection.target_component}")

# Start receiving messages
while True:
    msg = connection.recv_match(blocking=True)
    if msg:
        print(msg)
