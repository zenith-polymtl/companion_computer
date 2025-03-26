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
    "AeEnable": True,          # Disable auto exposure      # Fixed exposure time (in microseconds)
    "AnalogueGain": 1,        # Fixed analog gain
    "AwbEnable": True,         # Disable auto white balance
    "FrameDurationLimits": (16666, 16666),  # ~60 FPS
    "NoiseReductionMode": 0,    # Disable noise reduction
})
picam2.start()

time.sleep(2)  # Allow the camera to stabilize

def overlayed_grid_centered(frame, spacing=50):
    """
    Overlays a grid on the frame, centered at the midpoint of the frame.
    
    The grid lines are spaced every `spacing` pixels in both x and y 
    directions, with the first line drawn at the frame's center.
    """
    output_frame = frame.copy()
    height, width = output_frame.shape[:2]

    # Flip if needed (like in your example, flip vertically)
    flipped = cv2.flip(output_frame, 0)
    output_frame = cv2.flip(flipped, 1)

    # Find center coordinates of the frame
    center_x = width // 2
    center_y = height // 2

    # 1) Draw the CENTER lines
    # Vertical center line
    cv2.line(output_frame, (center_x, 0), (center_x, height), color=(255, 255, 255), thickness=1)
    # Horizontal center line
    cv2.line(output_frame, (0, center_y), (width, center_y), color=(255, 255, 255), thickness=1)

    # 2) Draw additional lines to the RIGHT of the center
    x = center_x + spacing
    while x < width:
        cv2.line(output_frame, (x, 0), (x, height), color=(255, 255, 255), thickness=1)
        cv2.putText(output_frame, f"{x}", (x, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        x += spacing

    # 3) Draw additional lines to the LEFT of the center
    x = center_x - spacing
    while x >= 0:
        cv2.line(output_frame, (x, 0), (x, height), color=(255, 255, 255), thickness=1)
        cv2.putText(output_frame, f"{x}", (x, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        x -= spacing

    # 4) Draw additional lines BELOW the center
    y = center_y + spacing
    while y < height:
        cv2.line(output_frame, (0, y), (width, y), color=(255, 255, 255), thickness=1)
        cv2.putText(output_frame, f"{y}", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y += spacing

    # 5) Draw additional lines ABOVE the center
    y = center_y - spacing
    while y >= 0:
        cv2.line(output_frame, (0, y), (width, y), color=(255, 255, 255), thickness=1)
        cv2.putText(output_frame, f"{y}", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        y -= spacing

    return output_frame


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
        _, buffer = cv2.imencode('.jpg', overlayed_grid_centered(frame, spacing = 100))
        frame = buffer.tobytes()

        # Yield the frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/stream')
def stream():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
