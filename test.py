from helper_funcs import *
import subprocess

nav = connect('/dev/serial0')
print("CONNECTED")
first = True

while True:
    if get_rc_value(nav,7) > 1600:
        print("Running")
        if first:
            process = subprocess.Popen(['python3', 'code/test_otherfile.py'])
            first = False

    else:
        if not first:
            process.terminate()
            process.wait()
            first = True
        print("Not running")

