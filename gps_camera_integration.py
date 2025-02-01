from helper_funcs import *
from analyze_tools import *

import numpy as np
from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import time
import math


master = connect('tcp:192.168.0.160:5762')
print("CONNECTED")

app = Flask(__name__)

picam = initialize_cam()

time.sleep(2)  # Allow the camera to stabilize


set_mode(master, 'GUIDED')
print("MODE SET TO GUIDED")


def convert_pixel_to_meters(x,y):
    return x/10, y/10

def compute_displacement(centroid, pos):
    
    drone_lat = pos[0]
    drone_lon = pos[1]
    hdg = pos[3]

    x_frame, y_frame = centroid[0], centroid[1]
    x_frame -= 1280/2
    y_frame -= 720/2

    delta_x, delta_y = convert_pixel_to_meters(x_frame, y_frame)

    # Earth radius in meters
    R_E = 6378137.0  # WGS-84 approximation
    
    # Compute absolute heading
    abs_heading = math.radians(hdg)

    delta_distance = np.sqrt(delta_x**2 +  delta_y**2)
    
    # Compute NED offsets
    north_offset = delta_distance * math.cos(abs_heading)
    east_offset = delta_distance * math.sin(abs_heading)

    # Convert latitude displacement
    delta_lat = (north_offset / R_E) * (180 / math.pi)
    
    # Convert longitude displacement (adjusted for latitude)
    delta_lon = (east_offset / (R_E * math.cos(math.radians(drone_lat)))) * (180 / math.pi)

    emitter_lat = drone_lat + delta_lat
    emitter_lon = drone_lon + delta_lon

    return emitter_lat, emitter_lon



def generate_frames():
    """
    Captures frames from the camera, processes them, and yields the processed frames for streaming.
    """
    while True:
        start_time = time.time()
        # Capture a frame using Picamera2
        frame = picam.capture_array()
        print('PIC')
        
        global_pos = get_global_pos(master)

        # Analyze the frame
        processed_frame, processing_time, centroid = analyze_frame_mean(frame, pos = global_pos, start_time=start_time)

        try: #À changer pour dk de moins paresseux ahah (en espèrant que je change et j'oublie pas plz)
            len(centroid)
            csv_good = True
        except:
            csv_good = False

        if csv_good:
            emitter_lat, emitter_lon = compute_displacement(centroid,pos = global_pos)
            insert_coordinates_to_csv('potentiel_sources.csv', (emitter_lat, emitter_lon))


        print(f"Analysis FPS : {1/processing_time:8.2f} Hz // Time taken by analysis : {processing_time:8.4f} seconds")


        # Encode the frame as JPEG
        _, buffer = cv2.imencode('.jpg', processed_frame)
        frame = buffer.tobytes()

        # Yield the frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    
@app.route('/stream')
def stream():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)



