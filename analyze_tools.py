import cv2
from sklearn.cluster import DBSCAN
import numpy as np
import time
from picamera2 import Picamera2
import matplotlib.pyplot as plt
import pandas as pd
from libcamera import controls

def initialize_cam(gain = 1, ExposureTime = 5000, lenspos = 8):
    
    # Initialize the Raspberry Pi Camera using Picamera2
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"size": (1280, 720)}))
    picam2.set_controls({
        "AeEnable": False,          # Disable auto exposure
        "ExposureTime": ExposureTime,       # Fixed exposure time (in microseconds)
        "AnalogueGain": gain,        # Fixed analog gain
        "AwbEnable": False,         # Disable auto white balance
        "FrameDurationLimits": (16666, 16666),  # ~60 FPS
        "NoiseReductionMode": 0,    # Disable noise reduction
        "AfMode": controls.AfModeEnum.Manual,
        "LensPosition": lenspos #Réciproque de x m
    })
    picam2.start()
    return picam2


def analyze_frame_DBSCAN(frame, min_points_in_cluster=3, scale_percent=10, threshold=253, eps=2, start_time=None):
    """
    Analyzes a single frame for white spots using DBSCAN clustering and overlays the centroid on the frame.
    """
    # Resize and convert to grayscale
    scale_factor = scale_percent / 100
    frame_resized = cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_NEAREST)
    frame_gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)

    # Threshold and collect points
    _, binary_frame = cv2.threshold(frame_gray, threshold, 255, cv2.THRESH_BINARY)
    points = np.column_stack(np.nonzero(binary_frame))
    if points.size == 0:
        return frame, time.time - start_time, None  # Return original frame if no points found

    # Apply DBSCAN clustering
    dbscan = DBSCAN(eps=eps, min_samples=min_points_in_cluster)
    labels = dbscan.fit_predict(points)

    # Find clusters and calculate centroids
    unique_labels = np.unique(labels)
    for label in unique_labels:
        if label == -1:
            continue  # Skip noise

        cluster_points = points[labels == label]

        # Calculate weighted centroid (intensities are binary in this case)
        centroid = np.mean(cluster_points, axis=0)

        # Scale centroid back to original frame size
        centroid = centroid / scale_factor

        total_time = time.time() - start_time
        # Visualize centroid
        output_frame = frame.copy()
        centroid_coords = tuple(map(int, centroid[::-1]))
        cv2.circle(output_frame, centroid_coords, 5, (0, 0, 255), -1)
        cv2.putText(output_frame, f"Centroid: {centroid_coords}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        return output_frame, total_time, centroid

    return frame, time.time() - start_time

def analyze_csv_dbscan(dataframe, eps=0.0000001, min_samples=3):
    """
    Reads a DataFrame with Est_Lat and Est_Lon, applies DBSCAN clustering,
    and visualizes the detected clusters.

    :param dataframe: Pandas DataFrame with 'Est_Lat' and 'Est_Lon' columns
    :param eps: Maximum distance between points in a cluster (adjust for GPS scale)
    :param min_samples: Minimum number of points in a cluster
    :return: DataFrame with clusters, DataFrame with centroids, List of cluster groups
    """
    # Ensure required columns exist
    if 'Est_Lat' not in dataframe.columns or 'Est_Lon' not in dataframe.columns:
        raise ValueError("CSV must contain 'Est_Lat' and 'Est_Lon' columns")
    
    coords = dataframe[['Est_Lat', 'Est_Lon']].to_numpy()

    # Apply DBSCAN clustering (Ensure correct input format)
    dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='haversine')
    labels = dbscan.fit_predict(np.radians(coords))  # Convert to radians

    dataframe['Cluster'] = labels  # Assign cluster labels to DataFrame

    # Compute centroids for clusters (excluding noise points labeled as -1)
    labels = np.array(labels)  # Ensure labels are a NumPy array
    unique_labels = set(labels)
    centroids = []
    cluster_groups = []

    for label in unique_labels:
        if label == -1:
            continue  # Skip noise points
        cluster_points = coords[labels == label]  # Extract cluster points
        centroid = np.mean(cluster_points, axis=0)
        centroids.append(centroid)
        cluster_groups.append(cluster_points.tolist())

    # Convert centroids to a DataFrame
    centroids_df = pd.DataFrame(centroids, columns=['Est_Lat', 'Est_Lon'])

    # Plot clusters and centroids
    plt.figure(figsize=(8, 6))
    for label in unique_labels:
        if label == -1:
            plt.scatter(dataframe[dataframe['Cluster'] == label]['Est_Lon'], 
                        dataframe[dataframe['Cluster'] == label]['Est_Lat'], 
                        c='grey', marker='x', label='Noise')
        else:
            plt.scatter(dataframe[dataframe['Cluster'] == label]['Est_Lon'], 
                        dataframe[dataframe['Cluster'] == label]['Est_Lat'], 
                        label=f'Cluster {label}')
    
    # Plot centroids
    if len(centroids) > 0:
        plt.scatter(centroids_df['Est_Lon'], centroids_df['Est_Lat'], 
                    c='red', marker='o', s=100, label='Centroids')
    
    plt.xlabel('Est_Lon')
    plt.ylabel('Est_Lat')
    plt.legend()
    plt.title('DBSCAN Clustering of GPS Coordinates')
    plt.show()
    
    return dataframe, centroids_df, cluster_groups, centroids

def analyze_frame_mean(frame, pos = None, scale_percent=10, threshold=150, start_time=None):
    """
    Analyzes a single frame for white spots using DBSCAN clustering and overlays the centroid on the frame.
    """
    # Resize and convert to grayscale
    scale_factor = scale_percent / 100
    frame_resized = cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_NEAREST)
    frame_gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)

    # Threshold and collect points
    _, binary_frame = cv2.threshold(frame_gray, threshold, 255, cv2.THRESH_BINARY)
    points = np.column_stack(np.nonzero(binary_frame))

    # Visualize centroid
    output_frame = frame.copy()
    if pos != None:
        cv2.putText(output_frame, f"GPS POS: {pos}", (10,60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            
    if points.size == 0:
        return output_frame, time.time() - start_time, None # Return original frame if no points found
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

        

