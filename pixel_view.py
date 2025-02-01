from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import time
from analyze_tools import *

app = Flask(__name__)


# Initialize the Raspberry Pi Camera using Picamera2
picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"size": (1280, 720)}))
picam2.set_controls({
    "AeEnable": False,          # Disable auto exposure
    "ExposureTime": 50000,       # Fixed exposure time (in microseconds)
    "AnalogueGain": 10,        # Fixed analog gain
    "AwbEnable": False,         # Disable auto white balance
    "FrameDurationLimits": (16666, 16666),  # ~60 FPS
    "NoiseReductionMode": 0,    # Disable noise reduction
})
picam2.start()

time.sleep(2)  # Allow the camera to stabilize

def overlayed_grid(frame, spacing=10):
    """
    Overlays a grid on the frame with the specified spacing.

    Parameters:
        frame (numpy.ndarray): The input frame.
        spacing (int): The spacing between grid lines in pixels.

    Returns:
        numpy.ndarray: The frame with the grid overlaid.
    """
    # Create a copy of the frame to draw the grid
    output_frame = frame.copy()
    height, width = frame.shape[:2]
    print(f" Shape : {height, width}")

    # Draw vertical grid lines
    for x in range(0, width, spacing):
        cv2.line(output_frame, (x, 0), (x, height), color=(255, 255, 255), thickness=1)
        cv2.putText(output_frame, f"{x}", (x, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Draw horizontal grid lines
    for y in range(0, height, spacing):
        cv2.line(output_frame, (0, y), (width, y), color=(255, 255, 255), thickness=1)
        cv2.putText(output_frame, f"{y}", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    

    return output_frame

def generate_frames():
    """
    Captures frames from the camera, processes them, and yields the processed frames for streaming.
    """
    while True:
        # Capture a frame using Picamera2
        frame = picam2.capture_array()

        # Analyze the frame


        # Encode the frame as JPEG
        _, buffer = cv2.imencode('.jpg', overlayed_grid(frame, spacing = 50))
        frame = buffer.tobytes()

        # Yield the frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/stream')
def stream():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
