from helper_func import *
from analyze_tools import initialize_cam
from analyze_tools import analyze_frame_mean
import numpy as np
import cv2
import time
import os
import csv
import math
import geopy.distance
import subprocess

mav = pymav()

# Initialize connection and camera
mav.connect('/dev/serial0')
print("CONNECTED")

picam = initialize_cam(gain = 1, ExposureTime=2000, lenspos = 8)
time.sleep(2)  # Allow the camera to stabilize



def csv_init():
    # Create a folder for today's data
    today = time.strftime("%Y-%m-%d_%H-%M")
    detection_dir = f"data/{today}/detection"
    no_detection_dir = f"data/{today}/no_detection"
    os.makedirs(detection_dir, exist_ok=True)
    os.makedirs(no_detection_dir, exist_ok=True)

    # CSV file path
    csv_file = os.path.join(detection_dir, "hotspots_metadata.csv")

    # Ensure CSV file has headers
    if not os.path.exists(csv_file):
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Image", "Drone_Lat", "Drone_Lon", "Drone_Alt", "Centroid_X", "Centroid_Y", "Est_Lat", "Est_Lon"])

    return detection_dir, no_detection_dir, csv_file


def convert_pixel_to_meters(x, y,d = 7):
    """ Converts pixel displacement to meters """
    coeff = 0.001279
    return x * coeff * d, y * coeff * d


def compute_displacement(centroid, pos):
    """Computes GPS displacement from pixel centroid position, considering heading and Earth's curvature"""
    
    if not isinstance(centroid, (list, tuple)) or len(centroid) != 2:
        raise ValueError("Invalid centroid: expected (x, y) tuple.")
    
    if not isinstance(pos, (list, tuple)) or len(pos) < 4:
        raise ValueError("Invalid position: expected (lat, lon, alt, hdg) tuple.")
    
    drone_lat, drone_lon, altitude, hdg = pos
    x_frame, y_frame = centroid

    # Adjust to center frame
    x_frame -= 1280 / 2
    y_frame -= 720 / 2  
    y_frame *= -1

    # Pixel to meters conversion with altitude consideration
    delta_x, delta_y = convert_pixel_to_meters(x_frame, y_frame, pos[2])

    abs_heading = math.radians(hdg)

    #Rotation matrix to convert the vector delta_x, delta_y of the relative emitter position, in drone frames of reference
    #
    north_offset = delta_x * math.cos(abs_heading) - delta_y * math.sin(abs_heading)
    east_offset = delta_x * math.sin(abs_heading) + delta_y * math.cos(abs_heading)

    new_lat = geopy.distance.distance(meters=north_offset).destination((drone_lat, drone_lon), 0).latitude
    new_lon = geopy.distance.distance(meters=east_offset).destination((drone_lat, drone_lon), 90).longitude

    return new_lat, new_lon


def capture_and_log(freq_max = 100):
    """ Captures images, analyzes frames, and logs relevant data """
    first = True
    while True:
        if mav.get_rc_value(7) > 1600:  # Only capture when the RC value is above 1600
            if first:
                detection_dir, no_detection_dir, csv_file = csv_init()
                # Start another script
                process = subprocess.Popen(['python3', 'code/analysis_and_kml.py'])
                first = False
                print("STARTED ANALYSIS")

            start_time = time.time()
            
            # Capture a frame
            frame = picam.capture_array()
            frame = cv2.flip(frame, 0)
            frame = cv2.flip(frame, 1)
            global_pos = mav.get_global_pos(heading=True)

            # Analyze the frame
            processed_frame, processing_time, centroid = analyze_frame_mean(frame, pos=global_pos, threshold=200, start_time=start_time)

            try:
                len(centroid)
                csv_good = True
            except:
                csv_good = False
                # Save image
                timestamp = time.strftime("%Y-%m-%d_%H-%M-%S") + f"-{int((time.time() % 1) * 100):02d}"
                img_path = os.path.join(no_detection_dir, f"{timestamp}.jpg")
                cv2.imwrite(img_path, processed_frame)

            if csv_good:
                est_lat, est_lon = compute_displacement(centroid, pos=global_pos)
                timestamp = time.strftime("%Y-%m-%d_%H-%M-%S") + f"-{int((time.time() % 1) * 100):02d}"

                # Save image
                img_path = os.path.join(detection_dir, f"{timestamp}.jpg")
                cv2.imwrite(img_path, processed_frame)

                # Append metadata to CSV
                with open(csv_file, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([timestamp, img_path, global_pos[0], global_pos[1], global_pos[2], centroid[0], centroid[1], est_lat, est_lon])
            print(f"Time taken :  {time.time()-start_time}")
        else:
            if not first:
                process.terminate()
                process.wait()
                first = True
            time.sleep(1)


if __name__ == '__main__':
    capture_and_log()
