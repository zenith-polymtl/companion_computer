from pymavlink import mavutil
import time
import numpy as np

# Helper functions
def is_near_waypoint(actual, target, threshold=2):
    """
    Check if the actual position is within a threshold distance of the target position.
    """
    return np.linalg.norm(np.array(actual) - np.array(target)) < threshold


def get_local_pos(connection, frequency_hz=60):
    """
    Retrieve the most recent LOCAL_POSITION_NED message.
    Request message interval only once and process the latest message.
    """

    # Send the message request once at the beginning
    message_request(connection, message_type=mavutil.mavlink.MAVLINK_MSG_ID_LOCAL_POSITION_NED, freq_hz=frequency_hz)

    while connection.recv_match(type='LOCAL_POSITION_NED', blocking=False):
        pass  # Discard old messages

    # Loop to receive the most recent message
    while True:
        msg = connection.recv_match(type='LOCAL_POSITION_NED', blocking=True) 
        if msg and msg.get_type() == "LOCAL_POSITION_NED":
            print(f"Position: X = {msg.x} m, Y = {msg.y} m, Z = {msg.z} m")
            return [msg.x, msg.y, msg.z]
        # Reduce busy-waiting and ensure responsiveness


def get_global_pos(connection, time_tag=False):

    message_request(connection, message_type=mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT, freq_hz=60)


    while connection.recv_match(type="GLOBAL_POSITION_INT", blocking=False):
        pass  # Discard old messages

    if time_tag == False:
        # Fetch the current global position
        while True:
            msg = connection.recv_match(blocking=True)
            if msg.get_type() == "GLOBAL_POSITION_INT":
                # Extract latitude, longitude, and relative altitude
                lat = msg.lat / 1e7  # Convert from int32 to degrees
                lon = msg.lon / 1e7  # Convert from int32 to degrees
                alt = msg.relative_alt / 1000.0  # Convert from mm to meters (relative altitude)
                hdg = msg.hdg/100

                print(f"Position: Lat = {lat}°, Lon = {lon}°, Alt = {alt} meters, hdg = {hdg}")
                return lat, lon, alt, hdg
    else:
        # Fetch the current global position with time tag
        while True:
            msg = connection.recv_match(blocking=True)
            if msg.get_type() == "GLOBAL_POSITION_INT":
                # Extract latitude, longitude, and relative altitude
                lat = msg.lat / 1e7  # Convert from int32 to degrees
                lon = msg.lon / 1e7  # Convert from int32 to degrees
                alt = msg.relative_alt / 1000.0  # Convert from mm to meters (relative altitude)
                hdg = msg.hdg

                timestamp = msg.time_boot_ms / 1000.0

                return timestamp, lat, lon, alt, hdg/100


def message_request(connection, message_type, freq_hz=10):
    interval_us = int(1e6 / freq_hz)  # Interval in microseconds
    # Send the command to set the message interval
    connection.mav.command_long_send(
        connection.target_system,  # Target system ID
        connection.target_component,  # Target component ID
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,  # Command to set message interval
        0,  # Confirmation
        message_type,  # Message ID for GLOBAL_POSITION_INT
        interval_us,  # Interval in microseconds
        0,
        0,
        0,
        0,
        0,  # Unused parameters
    )


def connect(ip_address='tcp:127.0.0.1:5762'):
    # Create the connection
    # Establish connection to MAVLink
    print('trying to connect')
    connection = mavutil.mavlink_connection(ip_address)
    print('Waiting for heartbeat...')
    connection.wait_heartbeat()
    print("Heartbeat received!")

    return connection


def set_mode(connection, mode):
    mode_id = connection.mode_mapping()[mode]
    connection.mav.set_mode_send(connection.target_system, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, mode_id)
    print(f"Setting mode to {mode}...")


def arm(connection):
    # Arm the vehicle
    print("Arming motors...")
    connection.mav.command_long_send(
        connection.target_system,
        connection.target_component,
        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
        0,
        1,
        0,
        0,
        0,
        0,
        0,
        0,
    )

    # Wait for arming confirmation
    connection.motors_armed_wait()
    print("Motors armed!")


def takeoff(connection, altitude=10):
    # Takeoff
    print(f"Taking off to {altitude} meters...")
    connection.mav.command_long_send(
        connection.target_system,
        connection.target_component,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        altitude,
    )
    print("Waiting for takeoff...")
    while is_near_waypoint(get_local_pos(connection)[2], -altitude) == False:
        time.sleep(0.1)


def connect_arm_takeoff(ip='tcp:127.0.0.1:5762', height=20):
    connection = connect(ip)

    # Set mode to GUIDED
    set_mode(connection,"GUIDED")

    arm(connection)

    takeoff(connection, height)


def local_target(connection, wp, acceptance_radius=20):
    connection.mav.set_position_target_local_ned_send(
        0,  # Time in milliseconds
        connection.target_system,
        connection.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        0b110111111000,  # Position mask
        wp[0],
        wp[1],
        wp[2],  # X (North), Y (East), Z (Down)
        0,
        0,
        0,  # No velocity
        0,
        0,
        0,  # No acceleration
        0,
        0,  # No yaw or yaw rate
    )

    # Wait for the waypoint to be reached
    print("Waiting for waypoint to be reached...")
    while not is_near_waypoint(get_local_pos(connection), wp, threshold=acceptance_radius):
        pass
    else:
        print("Waypoint reached!")


def RTL(connection):
    print("Returning to launch...")
    connection.mav.command_long_send(
        connection.target_system,
        connection.target_component,
        mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    while get_local_pos(connection)[2] > -1:
        time.sleep(0.1)
    else:
        connection.motors_disarmed_wait()
        print("Landed and motors disarmed!")

        connection.close()
        print("Connection closed. Mission Finished")

import csv

def insert_coordinates_to_csv(file_path, coordinates):
    """
    Inserts coordinates into a CSV file. If the file doesn't exist, it creates one with a header.
    
    Parameters:
        file_path (str): Path to the CSV file.
        coordinates (list of tuples): List of (latitude, longitude) coordinates.
        
    Example:
        insert_coordinates_to_csv("coordinates.csv", [(45.5017, -73.5673), (40.7128, -74.0060)])
    """
    # Check if the file exists
    try:
        with open(file_path, mode='r') as file:
            file_exists = True
    except FileNotFoundError:
        file_exists = False
    
    # Open the file in append mode
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # If the file doesn't exist, write the header
        if not file_exists:
            writer.writerow(["Latitude", "Longitude"])
        

        writer.writerow([coordinates[0], coordinates[1]])

def append_description_to_last_line(file_path, description):
    """
    Appends a description to the last line of a CSV file. The description is added in a new column.
    
    Parameters:
        file_path (str): Path to the CSV file.
        description (str): The description to append.
        
    Example:
        append_description_to_last_line("coordinates.csv", "City Center")
    """
    # Read the existing content of the CSV file
    rows = []
    try:
        with open(file_path, mode='r', newline='') as file:
            reader = csv.reader(file)
            rows = list(reader)
    except FileNotFoundError:
        print("Error: The file does not exist.")
        return
    
    # Check if there's at least one row (after header)
    if len(rows) <= 1:
        print("Error: No data rows to update.")
        return
    
    # Append the description to the last row
    last_row = rows[-1]
    last_row.append(description)
    
    # Write the updated rows back to the file
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)


def spiral_scan(connection, largeur_detection = 10, altitude = 10, rayon_scan = 100, safety_margin = 0, center = None):
    if center is None:
        pos = get_local_pos(connection)
    else:
        pos = center
    
    espacement = largeur_detection
    nombre_de_tours = rayon_scan / espacement

    rayon_scan += safety_margin

    # Spiral parameters
    theta_spiral = np.linspace(0, 2 * np.pi*nombre_de_tours, 100)
    b = espacement/(2*np.pi)
    r_spiral = b * theta_spiral
    x_spiral = r_spiral * np.cos(theta_spiral) + pos[0]
    y_spiral = r_spiral * np.sin(theta_spiral) + pos[1]

    start_time = time.time()

    for i in range(len(x_spiral)):
        wp = [x_spiral[i], y_spiral[i], -altitude]
        local_target(connection, wp, acceptance_radius=10)

    total_time = time.time() - start_time
    print("SCAN FINISHED")
    print(f"Total time taken : {total_time:.2f}")


def rectilinear_scan(connection, largeur_detection = 10, altitude = 10, rayon_scan = 100, safety_margin = 0, center = None):
    if center is None:
        pos = get_local_pos(connection)
    else:
        pos = center
    
    
    e = largeur_detection
    radius = rayon_scan
    safety_margin = 0
    radius += safety_margin
    x = []
    y = []
    high = True
    n_passes = int(2*radius/e)
    for n in range(n_passes):
        w = e*(1/2 + n)
        h = np.sqrt(radius**2 - (radius - w)**2)
        if high:
            x.append(-radius + w)
            y.append(h)
            x.append(-radius + w)
            y.append(-h)
            high = False
        else:
            x.append(-radius + w)
            y.append(-h)
            x.append(-radius + w)
            y.append(h)
            high = True

    start_time = time.time()

    for i in range(len(x)):
        wp = [x[i] + pos[0], y[i] + pos[1], -10]
        local_target(connection, wp, acceptance_radius=3)

    total_time = time.time() - start_time
    print("SCAN FINISHED")
    print(f"Total time: {total_time:.2f} seconds")