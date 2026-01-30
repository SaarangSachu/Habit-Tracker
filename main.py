import customtkinter as ctk
import threading
import time
from plyer import notification
from datetime import datetime

# Import Custom Modules
from database import Database
from components import HabitCard, Sidebar
from clock_widget import RealTimeClock 
from sounds import SoundManager  # <--- NEW IMPORT

# App Configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Winter Arc Tracker")
        self.geometry("950x650")
        
        # Initialize Backend Systems
        self.db = Database()
        self.sound = SoundManager() # <--- Initialize Sound
        
        # 1. TEST NOTIFICATION ON STARTUP
        print("--- STARTING APP ---")
        try:
            notification.notify(
                title="Winter Arc Tracker",
                message="App started! Notifications are working.",
                app_name="Winter Arc",
                timeout=5
            )
            print("✅ Test notification sent.")
        except Exception as e:
            print(f"❌ Notification failed: {e}")

        # Start Background Scheduler Thread
        self.stop_thread = False
        self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.thread.start()

        # UI Setup
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, self.navigate)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        
        self.show_dashboard()

    def run_scheduler(self):
        """Checks time every 10 seconds."""
        print("🕒 Scheduler thread started...")
        
        while not self.stop_thread:
            current_time = datetime.now().strftime("%H:%M")
            
            try:
                habits = self.db.get_habits()
                for (h_id, name, remind_time, is_done) in habits:
                    if remind_time and not is_done:
                        if remind_time == current_time:
                            print(f"🔔 MATCH FOUND: {name}")
                            
                            # 1. Play Alert Sound
                            self.sound.play_notification()  # <--- TRIGGER SOUND
                            
                            # 2. Show Windows Notification
                            notification.notify(
                                title="Time to Grind! ⚡",
                                message=f"Don't forget to: {name}",
                                app_name="Winter Arc",
                                timeout=10
                            )
                            time.sleep(60) # Wait 1 min to avoid spamming
            except Exception as e:
                print(f"Error in scheduler: {e}")
            
            time.sleep(10)

    def navigate(self, page_name):
        if page_name == "dashboard": self.show_dashboard()
        elif page_name == "analytics": self.show_analytics()

    def show_dashboard(self):
        self.clear_frame()
        
        # Header Container
        header_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Title
        ctk.CTkLabel(header_frame, text="Today's Focus", font=("Segoe UI", 32, "bold")).pack(side="left")
        
        # Real-Time Clock
        clock = RealTimeClock(header_frame)
        clock.pack(side="left", padx=20)
        
        # Add & Time Inputs
        ctk.CTkButton(header_frame, text="+ Add", width=80, height=35, command=self.add_habit_event).pack(side="right")
        
        self.add_entry = ctk.CTkEntry(header_frame, placeholder_text="New Habit...", width=200, height=35)
        self.add_entry.pack(side="right", padx=5)

        self.time_entry = ctk.CTkEntry(header_frame, placeholder_text="09:00", width=80, height=35)
        self.time_entry.pack(side="right", padx=5)
        
        # Progress Bar
        self.progress = ctk.CTkProgressBar(self.main_area, height=15, corner_radius=8)
        self.progress.pack(fill="x", pady=(0, 25))
        self.progress.set(0)

        # Habit List Container
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)
        self.load_habits_list()

    def load_habits_list(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        habits = self.db.get_habits()
        total = len(habits)
        done_count = 0

        for (h_id, name, remind_time, is_done) in habits:
            streak = self.db.get_streak(h_id)
            if is_done: done_count += 1
            
            display_time = remind_time if remind_time else ""
            
            # Create Card with all callbacks
            card = HabitCard(
                self.scroll_frame, h_id, name, display_time, is_done, streak, 
                self.toggle_habit, 
                self.delete_habit_event
            )
            card.pack(fill="x", pady=8)

        if total > 0: self.progress.set(done_count / total)
        else: self.progress.set(0)

    def toggle_habit(self, h_id, is_checked):
        # 1. Toggle DB
        self.db.toggle_habit(h_id, is_checked)
        
        # 2. Play Success Sound (Only if checking the box)
        if is_checked:
            self.sound.play_success() # <--- TRIGGER SOUND
            
        # 3. Reload UI
        self.load_habits_list()

    def delete_habit_event(self, h_id):
        self.db.delete_habit(h_id)
        self.load_habits_list()

    def add_habit_event(self):
        text = self.add_entry.get()
        time_val = self.time_entry.get().strip()
        
        # Format Time logic
        if time_val:
            try:
                valid_time = datetime.strptime(time_val, "%H:%M").strftime("%H:%M")
            except ValueError:
                print("Invalid time format! Use HH:MM")
                valid_time = ""
        else:
            valid_time = ""

        if text:
            self.db.add_habit(text, valid_time)
            self.add_entry.delete(0, "end")
            self.time_entry.delete(0, "end")
            self.show_dashboard()

    def show_analytics(self):
        self.clear_frame()
        ctk.CTkLabel(self.main_area, text="Activity Heatmap", font=("Segoe UI", 32, "bold")).pack(anchor="w", pady=(0, 30))
        
        heatmap_frame = ctk.CTkFrame(self.main_area, fg_color="#1a1a1a", corner_radius=15)
        heatmap_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        grid = ctk.CTkFrame(heatmap_frame, fg_color="transparent")
        grid.place(relx=0.5, rely=0.5, anchor="center")
        
        from datetime import date, timedelta
        data = self.db.get_activity_data()
        start = date.today() - timedelta(days=27)

        for i in range(28):
            day = start + timedelta(days=i)
            count = data.get(str(day), 0)
            
            if count == 0: color = "#2d2d2d"
            elif count <= 2: color = "#1e7e48"
            else: color = "#2CC985" 
            
            box = ctk.CTkFrame(grid, width=50, height=50, fg_color=color, corner_radius=4)
            box.grid(row=i//7, column=i%7, padx=6, pady=6)
            
            ctk.CTkLabel(box, text=str(day.day), font=("Arial", 10), text_color="white").place(relx=0.5, rely=0.5, anchor="center")

    def clear_frame(self):
        for widget in self.main_area.winfo_children(): widget.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()