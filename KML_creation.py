'''
Input du code suivant :
fichiers 'stock_source_feu' & 'stock_centroids'

Output du code suivant :
Création d'un fichier KML adapté aux requis de la compé.
Le KML contient l'analyse des hotspots et de la source du feu.

Date dernière itération : 2 avril 2025
Auteur : Laurent Ducharme
'''

import csv
import os
import simplekml
from time import sleep
import datetime as dt
import math
#from helper_funcs import haversine #pas nécessaire, la fct haversine est de la ligne 19 à 31 pour l'instant


def haversine(coord1, coord2):
    R = 6372800  # Earth radius in meters
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    phi1, phi2 = math.radians(lat1), math.radians(lat2) 
    dphi       = math.radians(lat2 - lat1)
    dlambda    = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + \
        math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))


liste_verif_stock_centroids = []
source_feu = []


#À commenter dès que "stock_source_feu" est créé
sourcefeudesc = [45.5100002,-73.6204909,"Sam Chicotte, le scout d'la forêt magique"]

output_dir = "companion_computer"
file_path = os.path.join(output_dir, 'stock_source_feu')

with open(file_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(sourcefeudesc)

#Fin du : À commenter


output_dir = "companion_computer"
file_path = os.path.join(output_dir, 'stock_source_feu')
with open(file_path, 'r', encoding='utf-8') as file:
    reader = csv.reader(file)
    for row in reader:
        source_feu = row

source_feu_coord = (source_feu[0], source_feu[1])

version_KML = 1

while True :
    liste_stock_centroids = []

    output_dir = "companion_computer"
    file_path = os.path.join(output_dir, 'stock_centroids')
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            liste_stock_centroids.append(tuple(row))
    #print(liste_stock_centroids)
    
    presumed_new_gps_coords = [x for x in liste_stock_centroids if x not in liste_verif_stock_centroids]
    #print(presumed_new_gps_coords)

    if presumed_new_gps_coords == []:
        print(f"==> Version {version_KML} du KML pas encore effectuée. Aucun nouveau point pour l'instant ({dt.datetime.now()}).")
        sleep(30)
        continue

    new_gps_coords = []
    liste_gps_remove = []

    if liste_verif_stock_centroids == []:
        new_gps_coords = presumed_new_gps_coords

    else:
        for gps_coord in presumed_new_gps_coords:
            for valid_centroid in liste_verif_stock_centroids:
                if haversine(gps_coord, valid_centroid) > 12:  #( haversine > tolérance en mètre), sujet à changement selon tests
                    new_gps_coords.append(gps_coord)

                if haversine(gps_coord, valid_centroid) < 4:   #prends moy. entre 2 pnts gps proches (si haversine < X mètres, jugé assez proche donc)
                    lat1, lon1 = gps_coord
                    lat2, lon2 = valid_centroid
                    moy_gps = ((lat1+lat2)/2, (lon1+lon2)/2)
                    new_gps_coords.append(moy_gps)
                    liste_gps_remove.append(valid_centroid)
    
    liste_verif_stock_centroids = [x for x in liste_verif_stock_centroids if x not in liste_gps_remove]
    

    liste_KML_ssource = liste_verif_stock_centroids + new_gps_coords

    kml = simplekml.Kml()

    lat, lon = source_feu_coord
    description_point = source_feu[2]
    point = kml.newpoint(name="Source", coords=[(lon, lat)])  # KML utilise (longitude, latitude)
    point.description = f"<![CDATA[<b>{description_point}</b>]]>"
    
    #print(liste_KML_ssource)
    
    nombre_hotspots = 0
    for coord in liste_KML_ssource:
        nombre_hotspots += 1
        lat, lon = coord
        name_point = f"Hotspot {nombre_hotspots}"
        point = kml.newpoint(name=name_point, coords=[(lon, lat)])  # KML utilise (longitude, latitude)

    nom_fichier_KML = f"{nombre_hotspots} hotspots - version {version_KML} - Équipe Zenith - Polytechnique Montréal.kml"

    version_KML += 1

    output_dir = "companion_computer"
    output_path = os.path.join(output_dir, nom_fichier_KML)
    kml.save(output_path)
    print(f"Fichier KML ({nom_fichier_KML}) créé ici à {dt.datetime.now()} : {output_path}")


    liste_verif_stock_centroids = liste_KML_ssource

    sleep(30)