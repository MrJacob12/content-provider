import os
import sys
import requests
import shutil
import tempfile
import subprocess
import hashlib

import dotenv
dotenv.load_dotenv()

SERVER_URL = os.getenv("API_URL")
UPDATE_INFO_URL = f"{SERVER_URL}/update_info/"
UPDATE_FILE_URL = f"{SERVER_URL}/download_update/"

def get_current_version():
    # Generate checksum of the current executable
    try:
        exe_dir = os.path.dirname(sys.executable)
        exe_path = os.path.join(exe_dir, 'game_updater.exe')
        print(f"Exe path: {exe_path}")
        checksum = hashlib.md5()
        with open(exe_path , "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                checksum.update(chunk)
            f.close()
        return checksum.hexdigest()
    except Exception as e:
        print(f"Error getting current version: {e}")
    return None

def check_for_update():
    current_version = get_current_version()
    print(f"Current version: {current_version}")
    try:
        response = requests.get(UPDATE_INFO_URL)
        if response.status_code == 200:
            update_info = response.json()
            latest_version = update_info.get('version')
            print(f"Latest version: {latest_version}")
            if latest_version != current_version:
                return latest_version
    except Exception as e:
        print(f"Error checking for update: {e}")
    return None

def download_update():
    try:
        response = requests.get(f"{UPDATE_FILE_URL}", stream=True)
        if response.status_code == 200:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
            return tmp_file.name
    except Exception as e:
        print(f"Error downloading update: {e}")
    return None

def replace_executable(update_file):
    try:
        exe_dir = os.path.dirname(sys.executable)
        exe_path = os.path.join(exe_dir, 'game_updater.exe')
        backup_path = exe_path + ".bak"
        
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(exe_path, backup_path)
        shutil.move(update_file, exe_path)
        os.chmod(exe_path, 0o755)
        print("Update successful. Restarting application.")
        subprocess.Popen([exe_path] + sys.argv[1:])
        sys.exit(0)
    except Exception as e:
        print(f"Error replacing executable: {e}")
        if os.path.exists(update_file):
            os.remove(update_file)

def main():
    exe_dir = os.path.dirname(sys.executable)
    exe_path = os.path.join(exe_dir, 'game_updater.exe')
    latest_version = check_for_update()
    if latest_version:
        print(f"New version available: {latest_version}")
        update_file = download_update()
        if update_file:
            replace_executable(update_file)
    else:
        subprocess.Popen([exe_path] + sys.argv[1:])
        print("No update available.")
        sys.exit(0)
if __name__ == "__main__":
    main()
