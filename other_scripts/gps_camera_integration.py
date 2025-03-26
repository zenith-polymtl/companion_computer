from companion_computer.helper_funcs_old import *
from analyze_tools import *

import numpy as np
from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import time
import math
import geopy

master = connect('/dev/ttyACM0')
print("CONNECTED")

app = Flask(__name__)


picam = initialize_cam(gain = 1, ExposureTime=2000)

time.sleep(2)  # Allow the camera to stabilize


def convert_pixel_to_meters(x, y, d = 7):
    """ Converts pixel displacement to meters """
    coeff = 0.001279
    return x *coeff* d, y *coeff*d

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
    y_frame *= -1  # Flip y-axis for Cartesian representation

    # Pixel to meters conversion with altitude consideration
    delta_x, delta_y = convert_pixel_to_meters(x_frame, y_frame, 7)

    abs_heading = math.radians(hdg)

    # Apply correct 2D rotation for heading, Might be really wrong, really depends on conventions used, to verify
    north_offset = delta_x * math.cos(abs_heading) - delta_y * math.sin(abs_heading)
    east_offset = delta_x * math.sin(abs_heading) + delta_y * math.cos(abs_heading)

    # Geodetic displacement using Haversine-based approach, put more effort in understanding this part cause I dont understand it
    new_position = geopy.distance.distance(meters=np.sqrt(north_offset**2 + east_offset**2)).destination(
        (drone_lat, drone_lon), math.degrees(abs_heading)
    )

    return new_position.latitude, new_position.longitude



def generate_frames():
    """
    Captures frames from the camera, processes them, and yields the processed frames for streaming.
    """
    while True:
        start_time = time.time()
        # Capture a frame using Picamera2
        frame = picam.capture_array()
        global_pos = get_global_pos(master)
        time_mesure = time.time()
        

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



