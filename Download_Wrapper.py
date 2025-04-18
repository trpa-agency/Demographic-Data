import subprocess
import time
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
script_path = os.path.join(script_dir, "Census_Download.py")  # Replace with your script's name

# Folder to monitor — change this to whatever folder you want to check
watch_folder = os.path.join(script_dir, 'Split_Lookup_Lists')

def is_folder_empty(folder_path):
    return len(os.listdir(folder_path)) == 0

while True:
        # Check if the folder is empty before running
    if is_folder_empty(watch_folder):
        print("Folder is empty. Stopping the script.")
        break

    try:
        # Run the script
        subprocess.run(["python", script_path], check=True, creationflags=subprocess.CREATE_NO_WINDOW,)
    except subprocess.CalledProcessError:
        print("Script crashed. Restarting...")
        time.sleep(5)  # Wait 5 seconds before restarting