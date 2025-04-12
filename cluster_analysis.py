from analyze_tools import analyze_csv_dbscan
from time import sleep
from pandas import read_csv
import os
import glob
import matplotlib
import time
matplotlib.use('Agg')  # Use headless (non-GUI) backend
import matplotlib.pyplot as plt
import csv

#python3 -m http.server 8000
#ensure que tu partes le serveur d'un terminal python de Shared_CSV (click droit, Open in intergrated terminal)
#créer un serveur sur le rasberryPi pour pouvoir faire une request de la GS.
script_start_time = time.time()
def get_latest_csv():
    """Finds the most recent CSV file in the data directory"""
    # Set the base directory
    base_dir = '/home/zenith/Documents/raspberry_pi/code/data/'

    # Recursively find all CSV files
    csv_files = glob.glob(os.path.join(base_dir, '**', '*.csv'), recursive=True)

    # Check if we found any
    if not csv_files:
        print("No CSV files found.")
    else:
        # Get the latest one by modification time
        return max(csv_files, key=os.path.getmtime)
folder_path = '/home/zenith/Documents/raspberry_pi/code/Shared_CSV/'
for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  # delete file or link
            elif os.path.isdir(file_path):
                # optional: remove subdirectories too
                import shutil
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

while True:
    try:
        latest_csv = get_latest_csv()
        

        if not latest_csv:
            print("No CSV file found! Waiting for data...")
            sleep(10)
            continue

        print(f"🔄 Trying to load data from: {latest_csv}")

        # Retry mechanism for file reading
        for attempt in range(5):  # Retry 5 times before giving up
            try:
                data = read_csv(latest_csv, encoding='utf-8')  # Force UTF-8 encoding
                break  # Success, exit loop
            except Exception as e:
                print(f"⚠️ Error reading CSV (attempt {attempt+1}): {e}")
                sleep(5)  # Wait before retrying
        else:
            print("❌ Failed to read CSV after multiple attempts.")
            sleep(30)
            continue

        # Debug: Print CSV headers and first few rows
        print(f"✅ CSV Headers: {list(data.columns)}")
        print("📊 Sample data:\n", data.head())

        # Analyze with DBSCAN
        clustered_data, centroids_df, cluster_groups, centroids = analyze_csv_dbscan(data, eps=0.0000001, min_samples=5)
        print(centroids)
        # Extract Latitude and Longitude
        lat, lon = data["Est_Lat"], data["Est_Lon"]
        print(f"Loaded {len(lat)} GPS points")

        # Plot raw data
        plt.figure(figsize=(8, 6))
        plt.scatter(lon, lat, c='blue', marker='o', label="Estimated Locations")

        if centroids:
            plt.scatter([c[1] for c in centroids], [c[0] for c in centroids], c='red', marker='o', label="Cluster Centers")

        plt.title("Estimated Hotspot Locations")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.legend()
        plot_path = os.path.join(os.path.dirname(os.path.dirname(latest_csv)), 'hotspots_plot.png')
        print(f"📊 Saving plot to: {plot_path}")
        plt.savefig(plot_path)
        print(f"📊 Plot saved: {plot_path}")

        print("✅ POINTS FOUND:")
        print(clustered_data)

    except FileNotFoundError:
        print("🚨 CSV file not found! Waiting for new data...")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

    sleep(2)

    '''
    Ajouté par Laurent pour créer fichier KML avec données centroids:
    '''

    output_dir = "/home/zenith/Documents/raspberry_pi/code/Shared_CSV"
    file_path = os.path.join(output_dir, f'stock_centroids.csv')

    parent_dir = os.path.dirname(latest_csv)
    grandparent_dir = os.path.dirname(parent_dir)

    # Get last modification time of the grandparent folder
    grandparent_mtime = os.path.getmtime(grandparent_dir)

    # Compare with script start time
    if grandparent_mtime < script_start_time:
        print(f"⏩ Skipping {latest_csv} because its grandparent folder was last modified before script started.")
        sleep(10)
    else:                 
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(centroids)  # Écrit plusieurs lignes

        sleep(10)