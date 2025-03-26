from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import time
from analyze_tools import *
app = Flask(__name__)
picam2 = initialize_cam(gain = 1, ExposureTime=2000)

time.sleep(2)  # Allow the camera to stabilize

def generate_frames():
    """
    Captures frames from the camera, processes them, and yields the processed frames for streaming.
    """
    while True:
        # Capture a frame using Picamera2
        start_time = time.time()
        frame = picam2.capture_array()

        # Analyze the frame
        processed_frame, processing_time, centroid = analyze_frame_mean(frame, start_time=start_time)


        print(f"Analysis FPS : {1/processing_time:8.2f} Hz // Time taken by analysis : {processing_time:8.4f} seconds")


        # Encode the frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Yield the frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/stream')
def stream():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
