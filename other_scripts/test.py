import time
import cv2
import numpy as np
from PIL import Image

def analyze_frame_mean(frame, colored_frame, pos=None, scale_percent=10, threshold=254, start_time=None):
    """
    Analyzes a single frame for white spots using DBSCAN clustering and overlays the centroid on the colored frame.
    """
    # Resize the grayscale frame for analysis (no need for grayscale conversion if the frame is already grayscale)
    scale_factor = scale_percent / 100
    frame_resized = cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_NEAREST)

    # Threshold and collect points
    _, binary_frame = cv2.threshold(frame_resized, threshold, 255, cv2.THRESH_BINARY)
    points = np.column_stack(np.nonzero(binary_frame))

    # Visualize centroid on the original colored frame
    output_frame = colored_frame.copy()
    if pos is not None:
        cv2.putText(output_frame, f"GPS POS: {pos}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    if points.size == 0:
        return output_frame, time.time() - start_time, None  # Return original frame if no points found
    else:
        # Calculate weighted centroid (intensities are binary in this case)
        centroid = np.mean(points, axis=0)

        # Scale centroid back to original frame size
        centroid = centroid / scale_factor

        total_time = time.time() - start_time
        
        centroid_coords = tuple(map(int, centroid[::-1]))
        cv2.circle(output_frame, centroid_coords, 5, (0, 0, 255), -1)
        cv2.putText(output_frame, f"Centroid: {centroid_coords}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        return output_frame, total_time, centroid_coords


# Load the PNG image (colored image)
image = Image.open('single_images/basic1.png')

# Convert the image to grayscale for analysis
gray_image = image.convert('L')  # 'L' mode is for grayscale

# Convert the grayscale image to a NumPy array for analysis
frame = np.array(gray_image)

# Convert the colored image to a NumPy array for visualization (keep original for overlay)
colored_frame = np.array(image)

# Analyze the frame for centroids
start_time = time.time()  # Store the start time
output_frame, total_time, centroid_coords = analyze_frame_mean(frame, colored_frame,threshold=150, start_time=start_time)

# Display the processed colored frame
cv2.imshow("Processed Image", output_frame)

# Wait until a key is pressed, then close the window
cv2.waitKey(0)  # Wait indefinitely until a key is pressed
cv2.destroyAllWindows()  # Close the window when done
