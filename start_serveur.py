import http.server
import socketserver
import os
import subprocess
import time

def kill_process_on_port(port):
    try:
        result = subprocess.check_output(
            f"lsof -i :{port} | grep LISTEN", shell=True, text=True
        )
        lines = result.strip().split('\n')
        for line in lines:
            parts = line.split()
            pid = parts[1]
            print(f"Killing process {pid} using port {port}...")
            subprocess.run(["kill", "-9", pid])
    except subprocess.CalledProcessError:
        print(f"No process found using port {port}.")

# === Configuration ===
PORT = 8000
DIRECTORY = "/home/zenith/Documents/raspberry_pi/code/Shared_CSV"

# Kill previous process using the port
kill_process_on_port(PORT)

# Wait a bit to make sure the port is released
time.sleep(1)

# Allow address reuse before binding
socketserver.TCPServer.allow_reuse_address = True

# Change to directory to serve
os.chdir(DIRECTORY)

# Set up HTTP handler
handler = http.server.SimpleHTTPRequestHandler

# Start server
with socketserver.TCPServer(("", PORT), handler) as httpd:
    print(f"Serving {DIRECTORY} at http://0.0.0.0:{PORT}")
    httpd.serve_forever()
