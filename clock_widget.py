import customtkinter as ctk
from datetime import datetime

class RealTimeClock(ctk.CTkLabel):
    def __init__(self, parent):
        super().__init__(
            parent, 
            text="00:00 AM", 
            font=("Segoe UI", 24, "bold"), 
            text_color="#2CC985"  # Matches your theme
        )
        self.update_clock()

    def update_clock(self):
        # Get time in 12-hour format with AM/PM (e.g., "02:30 PM")
        current_time = datetime.now().strftime("%I:%M %p")
        
        # Remove leading zero if you prefer "2:30" over "02:30" (Optional)
        # if current_time.startswith("0"):
        #     current_time = current_time[1:]

        self.configure(text=current_time)
        
        # Schedule this function to run again in 1000ms (1 second)
        self.after(1000, self.update_clock)