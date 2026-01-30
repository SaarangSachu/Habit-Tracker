import os
import sys
import threading
from playsound import playsound

# Helper to find files inside the .exe
def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SoundManager:
    def __init__(self):
        self.enabled = True
        self.is_muted = False  # Added missing mute flag for consistency

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        return self.is_muted

    def play_success(self):
        if self.is_muted: return
        self._play("success.mp3")

    def play_notification(self):
        if self.is_muted: return
        self._play("notification.mp3")

    def _play(self, filename):
        # 1. Get the correct path (works in .exe and VS Code)
        file_path = resource_path(os.path.join("sounds", filename))
        
        # 2. Check if file exists to prevent errors
        if os.path.exists(file_path):
            try:
                # 3. Threading ensures the app doesn't freeze while playing
                threading.Thread(target=playsound, args=(file_path,), daemon=True).start()
            except Exception as e:
                print(f"Error playing sound: {e}")
        else:
            print(f"⚠️ Sound file not found: {file_path}")