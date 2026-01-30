import os
import threading
from playsound import playsound

class SoundManager:
    def __init__(self):
        self.enabled = True
        # Define the path to the sounds folder
        # This gets the current folder where this file is, and adds 'sounds' to it
        self.sound_folder = os.path.join(os.path.dirname(__file__), "sounds")

    def play_success(self):
        # We look for the file inside the sounds folder
        file_path = os.path.join(self.sound_folder, "success.mp3")
        threading.Thread(target=self._play, args=(file_path,), daemon=True).start()

    def play_notification(self):
        file_path = os.path.join(self.sound_folder, "notification.mp3")
        threading.Thread(target=self._play, args=(file_path,), daemon=True).start()

    def _play(self, file_path):
        if os.path.exists(file_path):
            try:
                playsound(file_path)
            except Exception as e:
                print(f"Error playing sound: {e}")
        else:
            print(f"⚠️ Sound file not found: {file_path}")