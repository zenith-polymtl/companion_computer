from analyze_tools import analyze_csv_dbscan
from time import sleep
from pandas import read_csv
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use headless (non-GUI) backend
import matplotlib.pyplot as plt

while True:
    # Load CSV
    try:
        data = read_csv('potentiel_sources.csv')

        # Ensure required columns exist
        if 'Latitude' not in data.columns or 'Longitude' not in data.columns:
            raise ValueError("CSV must contain 'Latitude' and 'Longitude' columns")

        # Ensure there's data in the CSV
        if data.empty:
            print("CSV is empty! Waiting for data...")
            sleep(30)
            exit()

        


        # Analyze with DBSCAN
        clustered_data, centroids_df, cluster_groups, centroids = analyze_csv_dbscan(data, eps=0.00000008, min_samples=5)

        # Extract Latitude and Longitude
        lat, lon = data['Latitude'], data['Longitude']
        print(lat,lon,centroids)

        # Plot raw data
        plt.figure(figsize=(8, 6))
        plt.scatter(lon, lat, c='blue', marker='o')  # Longitude (X-axis), Latitude (Y-axis)

        plt.scatter([centre[1] for centre in centroids], [centre[0] for centre in centroids], c='red', marker='o')  # Longitude (X-axis), Latitude (Y-axis)
        plt.title("Raw Data Points")
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.savefig('data')

        

        print("✅ POINTS FOUND:")
        print(clustered_data)

    except FileNotFoundError:
        print("CSV file not found! Make sure 'potentiel_sources.csv' exists.")
    except ValueError as e:
        print(f"ERROR: {e}")

    # Sleep before next cycle
    sleep(30)
