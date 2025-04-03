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

def get_latest_csv():
    """Finds the most recent CSV file in the data directory"""
    data_dirs = sorted(glob.glob("data/*"), reverse=True)  # Sort directories by date
    for directory in data_dirs:
        csv_files = sorted(glob.glob(os.path.join(directory, "*.csv")), reverse=True)
        if csv_files:
            return csv_files[0]  # Return latest CSV file
    return None

while True:
    try: #peutêtre a couper si je veux juste un csv précis / mettre le lien dans lastest_csv ligne 34
        #latest_csv = get_latest_csv()

        '''  if not latest_csv:
            print("No CSV file found! Waiting for data...")
            sleep(30)
            continue'''

        #print(f"🔄 Trying to load data from: {latest_csv}")
        import os

        file_path = "/home/avatar/companion_computer/ demo_sauvergarde/2025-02-06/hotspots_metadata.csv"
        if not os.path.exists(file_path):
             print(f"❌ Le fichier n'existe pas : {file_path}")
    # Ajouter une logique ici pour gérer ce cas, par exemple créer un fichier vide ou quitter.

        # Retry mechanism for file reading
        for attempt in range(5):  # Retry 5 times before giving up
            try: # la
                data = read_csv("/home/avatar/companion_computer/ demo_sauvergarde/2025-02-06/hotspots_metadata.csv", encoding='utf-8')  # Force UTF-8 encoding
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

        # Ensure required columns exist
        if "Est_Lat" not in data.columns or "Est_Lon" not in data.columns:
            print(f"❌ Missing expected columns in {latest_csv}. Found: {list(data.columns)}")
            sleep(30)
            continue

        if data.empty:
            print("🚨 CSV is empty! Waiting for data...")
            sleep(30)
            continue

        # Analyze with DBSCAN
        clustered_data, centroids_df, cluster_groups, centroids = analyze_csv_dbscan(data, eps=0.00000008, min_samples=5)

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
        plot_path = os.path.join("data", "hotspots_plot.png")
        plt.savefig(plot_path)
        print(f"📊 Plot saved: {plot_path}")

        print("✅ POINTS FOUND:")
        print(clustered_data)

    except FileNotFoundError:
        print("🚨 CSV file not found! Waiting for new data...")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

    print(centroids)


    '''
    Ajouté par Laurent pour créer fichier kml avec données centroids:
    '''
    output_dir = "companion_computer"
    file_path = os.path.join(output_dir, 'stock_centroids')
                             
    with open(file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(centroids)  # Écrit plusieurs lignes

    sleep(30)

