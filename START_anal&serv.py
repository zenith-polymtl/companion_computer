import subprocess
import time
import os


# Chemins absolus vers les scripts
base_dir = "/home/zenith/Documents/raspberry_pi/code"
serveur_script = os.path.join(base_dir, "start_serveur.py")
analysis_script = os.path.join(base_dir, "cluster_analysis.py")

# Lancer les scripts
analysis_process = subprocess.Popen(["python3", analysis_script])
time.sleep(30)
serveur_process = subprocess.Popen(["python3", serveur_script])

print("Les deux scripts sont lancés. Appuie sur Entrée pour les arrêter.")
input()

# Fermer les deux scripts
serveur_process.terminate()
analysis_process.terminate()

print("Les processus ont été arrêtés.")