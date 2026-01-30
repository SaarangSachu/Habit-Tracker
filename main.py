import customtkinter as ctk
import threading
import time
from plyer import notification
from datetime import datetime

from database import Database
from components import HabitCard, Sidebar
# --- NEW IMPORT ---
from clock_widget import RealTimeClock 

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Winter Arc Tracker")
        self.geometry("950x650")
        self.db = Database()
        
        # (Notification test code remains here...)
        try:
            notification.notify(title="Winter Arc", message="App started!", timeout=2)
        except: pass

        self.stop_thread = False
        self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.thread.start()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, self.navigate)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        
        self.show_dashboard()

    # (Scheduler function remains exactly the same...)
    def run_scheduler(self):
        while not self.stop_thread:
            current_time = datetime.now().strftime("%H:%M")
            # print(f"Checking {current_time}...") 
            try:
                habits = self.db.get_habits()
                for (h_id, name, remind_time, is_done) in habits:
                    if remind_time and not is_done:
                        if remind_time == current_time:
                            notification.notify(
                                title="Time to Grind! ⚡",
                                message=f"Don't forget: {name}",
                                timeout=10
                            )
                            time.sleep(60)
            except: pass
            time.sleep(10)

    def navigate(self, page_name):
        if page_name == "dashboard": self.show_dashboard()
        elif page_name == "analytics": self.show_analytics()

    # --- UPDATED DASHBOARD FUNCTION ---
    def show_dashboard(self):
        self.clear_frame()
        
        # Header Container
        header_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        # 1. Title
        ctk.CTkLabel(header_frame, text="Today's Focus", font=("Segoe UI", 32, "bold")).pack(side="left")
        
        # 2. NEW: Real-Time Clock (Placed in the center/left)
        clock = RealTimeClock(header_frame)
        clock.pack(side="left", padx=20)
        
        # 3. Inputs (Right side)
        ctk.CTkButton(header_frame, text="+ Add", width=80, height=35, command=self.add_habit_event).pack(side="right")
        
        self.add_entry = ctk.CTkEntry(header_frame, placeholder_text="New Habit...", width=200, height=35)
        self.add_entry.pack(side="right", padx=5)

        self.time_entry = ctk.CTkEntry(header_frame, placeholder_text="09:00", width=80, height=35)
        self.time_entry.pack(side="right", padx=5)
        
        # Progress Bar
        self.progress = ctk.CTkProgressBar(self.main_area, height=15, corner_radius=8)
        self.progress.pack(fill="x", pady=(0, 25))
        self.progress.set(0)

        # Habit List
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)
        self.load_habits_list()

    # (All other functions remain exactly the same...)
    def load_habits_list(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        habits = self.db.get_habits()
        total = len(habits)
        done_count = 0
        for (h_id, name, remind_time, is_done) in habits:
            streak = self.db.get_streak(h_id)
            if is_done: done_count += 1
            display_time = remind_time if remind_time else ""
            card = HabitCard(self.scroll_frame, h_id, name, display_time, is_done, streak, self.toggle_habit)
            card.pack(fill="x", pady=8)
        if total > 0: self.progress.set(done_count / total)
        else: self.progress.set(0)

    def toggle_habit(self, h_id, is_checked):
        self.db.toggle_habit(h_id, is_checked)
        self.load_habits_list()

    def add_habit_event(self):
        text = self.add_entry.get()
        time_val = self.time_entry.get().strip()
        # Ensure format is saved as 24h for the backend logic (HH:MM)
        # Even if user wants 12h clock, backend logic usually prefers 24h for easy comparison
        valid_time = ""
        if time_val:
            try:
                valid_time = datetime.strptime(time_val, "%H:%M").strftime("%H:%M")
            except: pass
            
        if text:
            self.db.add_habit(text, valid_time)
            self.add_entry.delete(0, "end")
            self.time_entry.delete(0, "end")
            self.show_dashboard()

    def show_analytics(self):
        self.clear_frame()
        # (Your existing analytics code)

    def clear_frame(self):
        for widget in self.main_area.winfo_children(): widget.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()