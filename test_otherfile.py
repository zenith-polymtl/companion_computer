import time

# File to store the integers
file_path = 'output.txt'

# Start counting from 1
count = 1

with open(file_path, 'w') as f:
    while True:
        f.write(f"{count}\n")   # Write the integer to the file
        f.flush()               # Ensure it's written immediately to disk
        print(f"Wrote: {count}")
        count += 1
        time.sleep(1)           # Wait for 1 second before writing the next integer
