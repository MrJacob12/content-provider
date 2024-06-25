import os
import json
import hashlib
import logging
import threading
import time
import requests
import customtkinter
import datetime
from tkinter import filedialog

customtkinter.set_appearance_mode("System")  # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

import dotenv
dotenv.load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SERVER_URL = os.getenv("API_URL")
LOCAL_DIR = "./game/"

class App:
    def __init__(self, root):
        self.root = root
        self.project = ""
        self.project_name = ""
        self.local_dir = ""

        #! Server Status Section
        self.server_status_label = customtkinter.CTkLabel(root, text="Server Status: Unknown", font=("Ubuntu", 12, "bold"))
        self.server_status_label.pack(pady=5)

        #! Top Section
        self.label_project = customtkinter.CTkLabel(root, text="Enter Project ID:", font=("Ubuntu", 12, "bold"))
        self.label_project.pack(pady=5)
        
        self.entry_project = customtkinter.CTkEntry(root, width=250, font=("Ubuntu", 12))     
        self.entry_project.pack(pady=5)

        self.select_dir_button = customtkinter.CTkButton(
            root, text="Select Directory", command=self.select_directory, font=("Ubuntu", 12, "bold")
        )
        self.select_dir_button.pack(pady=5)

        self.selected_dir_label = customtkinter.CTkLabel(root, text="Selected Directory: None", font=("Ubuntu", 12, "bold"))
        self.selected_dir_label.pack(pady=5)
        #! Middle Section
        self.update_button = customtkinter.CTkButton(
            root, text="Update Game", command=self.update_game, font=("Ubuntu", 12, "bold")
        )
        self.update_button.pack(pady=10)

        self.info_frame = customtkinter.CTkFrame(root)
        self.info_frame.pack(pady=10, fill=customtkinter.BOTH, expand=True)

        self.project_name_label = customtkinter.CTkLabel(self.info_frame, text="Project Name: - ", font=("Ubuntu", 12, "bold"))
        self.project_name_label.pack()

        self.file_size_label = customtkinter.CTkLabel(self.info_frame, text="File Size: - ", font=("Ubuntu", 12, "bold"))
        self.file_size_label.pack()

        self.download_speed_label = customtkinter.CTkLabel(self.info_frame, text="Download Speed: - ", font=("Ubuntu", 12, "bold"))
        self.download_speed_label.pack()

        self.loading_label = customtkinter.CTkLabel(root, text="", font=("Ubuntu", 14, "bold"))
        self.loading_label.pack(pady=1)

        #! Bottom Section
        self.text_area = customtkinter.CTkTextbox(root, height=200, width=500, font=("Ubuntu", 12))
        self.text_area.pack(pady=10, fill=customtkinter.BOTH, expand=True)

        self.scrollbar = customtkinter.CTkScrollbar(root, command=self.text_area.yview)
        self.scrollbar.pack(side=customtkinter.RIGHT, fill=customtkinter.Y)
        self.text_area.configure(yscrollcommand=self.scrollbar.set)

        #! Loading animation setup
        self.loading_animation_frames = ["|", "/", "-", "\\"]
        self.current_animation_frame = 0
        self.loading_animation_interval = 200  # in milliseconds

        self.server_status = False
        self.check_server_status()
        self.completed_files = {}  # Dictionary to store completed files information

    def select_directory(self):
        self.local_dir = filedialog.askdirectory()
        if self.local_dir:
            self.selected_dir_label.configure(text=f"Selected Directory: {self.local_dir}")
            self.text_area.insert(customtkinter.END, f"Selected Directory: {self.local_dir}\n")
        else:
            self.text_area.insert(customtkinter.END, "No directory selected.\n")

    def update_game(self):
        self.project = self.entry_project.get().strip()
        if not self.project:
            self.text_area.insert(customtkinter.END, "Please enter a Project ID.\n")
            return
        if not self.local_dir:
            self.text_area.insert(customtkinter.END, "Please select a local directory.\n")
            return

        self.text_area.delete("1.0", customtkinter.END)  # Clear previous output
        self.update_button.configure(
            state=customtkinter.DISABLED
        )  # Disable update button during update
        self.project_name_label.configure(text="Project Name: - ")
        self.file_size_label.configure(text="File Size: - ")
        self.download_speed_label.configure(text="Download Speed: - ")

        # Start loading animation
        self.animate_loading()

        # Fetch project information from server
        self.fetch_project_info()

        # Start update process in a separate thread
        update_thread = threading.Thread(target=self.update_game_files_threaded)
        update_thread.start()

    def animate_loading(self):
        self.loading_label.configure(
            text=self.loading_animation_frames[self.current_animation_frame]
        )
        self.current_animation_frame = (self.current_animation_frame + 1) % len(
            self.loading_animation_frames
        )
        self.root.after(self.loading_animation_interval, self.animate_loading)

    def fetch_project_info(self):
        try:
            response = requests.get(f"{SERVER_URL}/files_info/{self.project}/")
            if response.status_code == 200:
                info = response.json()
                project_name = info.get("project_name", "Unknown")
                self.project_name_label.configure(text=f"Project Name: {project_name}")
            else:
                self.text_area.insert(
                    customtkinter.END,
                    f"Error fetching project information: {response.status_code}\n",
                )
        except Exception as e:
            self.text_area.insert(customtkinter.END, f"An error occurred: {str(e)}\n")

    def update_game_files_threaded(self):
        try:
            response = requests.get(f"{SERVER_URL}/files_info/{self.project}/")
            if response.status_code == 200:
                files_info = response.json()
                self.project_name = files_info.get("project_name", "Unknown")
                self.update_game_files(files_info)
                self.text_area.insert(customtkinter.END, "\nUpdate complete.\n")
                self.text_area.see(customtkinter.END)
                self.text_area.update_idletasks()
            else:
                self.text_area.insert(
                    customtkinter.END,
                    f"Error fetching files information: {response.status_code}\n",
                )
        except Exception as e:
            self.text_area.insert(customtkinter.END, f"An error occurred: {str(e)}\n")
        
        # in script path write to projects_list.json
        projects_list = {}
        if not os.path.exists("projects_list.json"):
            projects_list = {}
        else:
            projects_list = json.load(open("projects_list.json", "r"))
        projects_list[self.project_name] = self.project
        with open("projects_list.json", "w") as f:
            json.dump(projects_list, f, indent=4)
        self.update_button.configure(
            state=customtkinter.NORMAL
        )  # Re-enable update button after update
        self.loading_label.configure(text="")

    def update_game_files(self, files_info):
        project_name = files_info.get("project_name", "Unknown")
        project_dir = os.path.join(self.local_dir, project_name)
        completed_files_path = os.path.join(project_dir, "completed_files.json")

        if not os.path.exists(project_dir):
            os.makedirs(project_dir, exist_ok=True)

        self.completed_files = self.load_completed_files(completed_files_path)

        for file_name, file_info in files_info["files"].items():
            local_file_dir = os.path.join(project_dir, os.path.dirname(file_name))
            if not os.path.exists(local_file_dir):
                os.makedirs(local_file_dir, exist_ok=True)

            local_file_path = os.path.join(project_dir, file_name)
            server_checksum = file_info.get("checksum")
            local_checksum = self.completed_files.get(file_name)

            if local_checksum and local_checksum == server_checksum:
                self.text_area.insert(customtkinter.END, f"{file_name} is up to date.\n")
                continue

            try:
                file_size = file_info.get("size", 0)
                self.download_file_with_speed(
                    f"{SERVER_URL}/files/",
                    {"project": self.project, "filename": file_name},
                    local_file_path,
                    file_size,
                )
                self.completed_files[file_name] = server_checksum
                self.save_completed_files(completed_files_path)
                self.text_area.insert(customtkinter.END, f"Downloaded {file_name}\n")
                self.text_area.see(customtkinter.END)
                self.text_area.update_idletasks()
            except Exception as e:
                self.text_area.insert(
                    customtkinter.END, f"Error downloading {file_name}: {str(e)}\n"
                )
                self.text_area.see(customtkinter.END)
                self.text_area.update_idletasks()

    def download_file_with_speed(self, url, data, local_file_path, file_size):
        response = requests.post(url, json=data, stream=True)
        total_length = int(response.headers.get("content-length", 0))

        start_time = time.time()
        downloaded = 0

        with open(local_file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=16384):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)

                    # Calculate download speed
                    elapsed_time = time.time() - start_time
                    if elapsed_time != 0:
                        download_speed = downloaded / (
                            1024 * 1024 * elapsed_time
                        )  # MB/s
                    else:
                        download_speed = 0  # or some other value that makes sense in your context
                    self.download_speed_label.configure(
                        text=f"Download Speed: {download_speed:.2f} MB/s"
                    )
                    self.file_size_label.configure(
                        text=f"File Size: {downloaded/(1024*1024):.2f} MB / {(total_length / (1024 * 1024)):.2f} MB"
                    )
                    # Update UI
                    self.root.update_idletasks()
            self.root.update_idletasks()

    def load_completed_files(self, path):
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return {}

    def save_completed_files(self, path):
        with open(path, "w") as f:
            json.dump(self.completed_files, f, indent=4)

    def check_server_status(self):
        try:
            response = requests.get(f"{SERVER_URL}/status")
            if response.status_code == 200:
                self.server_status = True
                self.server_status_label.configure(text=f"Server Status: Online ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
                self.server_status_label.configure(text_color="green", font=("Ubuntu", 12, "bold"))
            else:
                self.server_status = False
                self.server_status_label.configure(text=f"Server Status: Offline ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
                self.server_status_label.configure(text_color="red", font=("Ubuntu", 12, "bold"))
        except Exception as e:
            self.server_status = False
            self.server_status_label.configure(text=f"Server Status: Error ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
            self.server_status_label.configure(text_color="red", font=("Ubuntu", 12, "bold"))
        self.root.update_idletasks()
        # Schedule the next check after 30 seconds
        self.root.after(30000, self.check_server_status)

if __name__ == "__main__":
    root = customtkinter.CTk()
    root.title("Game Updater")
    root.geometry("600x600")
    app = App(root)
    root.mainloop()
