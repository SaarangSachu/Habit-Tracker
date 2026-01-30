import customtkinter as ctk
import threading
import time
from plyer import notification
from datetime import datetime

# Import Custom Modules
from database import Database
from components import HabitCard, Sidebar
from clock_widget import RealTimeClock 
from sounds import SoundManager
from analytics import AnalyticsPanel  # New Analytics Module

# App Configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Winter Arc Tracker v3.0 (RPG Edition)")
        self.geometry("1100x700")
        
        # Initialize Backend Systems
        self.db = Database()
        self.sound = SoundManager()
        
        # Gamification State
        self.total_xp = 0
        self.level = 1
        self.next_level_xp = 100
        
        # UI State
        self.editing_id = None
        self.current_filter = "All"
        
        # Start Background Scheduler Thread
        self.stop_thread = False
        self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.thread.start()

        # Grid Layout Configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 1. Calculate Initial XP
        self.calculate_xp()
        
        # 2. Sidebar (Initialized via refresh to pass XP data)
        self.sidebar = None
        self.refresh_sidebar()

        # 3. Main Content Area
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        
        # Show Dashboard by default
        self.show_dashboard()

    def calculate_xp(self):
        """Calculates player level based on total completed tasks."""
        # 1 Task = 10 XP
        completions = self.db.get_total_completions()
        self.total_xp = completions * 10
        
        # Leveling Logic
        if self.total_xp < 100:
            self.level = 1
            self.next_level_xp = 100
        elif self.total_xp < 300:
            self.level = 2
            self.next_level_xp = 300
        elif self.total_xp < 600:
            self.level = 3
            self.next_level_xp = 600
        elif self.total_xp < 1000:
            self.level = 4
            self.next_level_xp = 1000
        else:
            self.level = 5
            self.next_level_xp = 5000 # God Mode

    def refresh_sidebar(self):
        """Re-draws the sidebar to update the XP bar."""
        if self.sidebar:
            self.sidebar.destroy()
            
        self.sidebar = Sidebar(
            self, 
            nav_callback=self.navigate, 
            total_xp=self.total_xp, 
            level=self.level, 
            next_level_xp=self.next_level_xp, 
            theme_callback=self.change_theme
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

    def change_theme(self, theme_name):
        """Callback for unlocking themes."""
        if theme_name == "cyberpunk":
            # For now, we simulate the theme switch
            ctk.set_default_color_theme("dark-blue") 
            notification.notify(title="Theme Unlocked!", message="Cyberpunk mode active.", timeout=3)

    def run_scheduler(self):
        """Background thread to check for time-based reminders."""
        print("🕒 Scheduler thread started...")
        while not self.stop_thread:
            current_time = datetime.now().strftime("%H:%M")
            try:
                # We check ALL habits regardless of current filter
                habits = self.db.get_habits(category_filter="All")
                
                # Unpack the 7 values returned by the updated SQL query
                for (h_id, name, remind_time, cat, target, is_done, progress) in habits:
                    if remind_time and not is_done:
                        if remind_time == current_time:
                            print(f"🔔 MATCH FOUND: {name}")
                            
                            self.sound.play_notification()
                            
                            notification.notify(
                                title="Time to Grind! ⚡",
                                message=f"Don't forget to: {name}",
                                timeout=10
                            )
                            time.sleep(60) # Prevent spamming for the same minute
            except Exception as e:
                print(f"Scheduler error: {e}")
            
            time.sleep(10)

    def navigate(self, page_name):
        if page_name == "dashboard": self.show_dashboard()
        elif page_name == "analytics": self.show_analytics()

    def show_dashboard(self):
        self.clear_frame()
        
        # --- HEADER ---
        header_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header_frame, text="Today's Focus", font=("Segoe UI", 32, "bold")).pack(side="left")
        RealTimeClock(header_frame).pack(side="left", padx=20)

        # --- CONTROLS (Add/Edit) ---
        control_frame = ctk.CTkFrame(self.main_area, fg_color="#2b2b2b", corner_radius=10)
        control_frame.pack(fill="x", pady=(0, 20), ipady=5)

        # 1. Name Input
        self.name_entry = ctk.CTkEntry(control_frame, placeholder_text="Habit Name...", width=200)
        self.name_entry.pack(side="left", padx=(15, 5), pady=10)
        
        # 2. Category Dropdown
        self.cat_var = ctk.StringVar(value="General")
        ctk.CTkComboBox(control_frame, values=["General", "Health", "Work", "Learning"], 
                        variable=self.cat_var, width=100, state="readonly").pack(side="left", padx=5)

        # 3. Frequency Dropdown
        self.freq_var = ctk.StringVar(value="Daily")
        freq_options = ["Daily", "1x / Week", "2x / Week", "3x / Week", "4x / Week", "5x / Week"]
        ctk.CTkComboBox(control_frame, values=freq_options, 
                        variable=self.freq_var, width=110, state="readonly").pack(side="left", padx=5)

        # 4. Time Input
        ctk.CTkLabel(control_frame, text="At:", text_color="grey").pack(side="left", padx=(10, 2))
        self.time_entry = ctk.CTkEntry(control_frame, placeholder_text="09:00", 
                                       placeholder_text_color="#AAAAAA", width=70)
        self.time_entry.pack(side="left", padx=2)

        # 5. Add/Save Button
        self.action_btn = ctk.CTkButton(control_frame, text="+ Add", width=80, command=self.save_habit_event)
        self.action_btn.pack(side="left", padx=15)
        
        # Cancel Button (Hidden initially)
        self.cancel_btn = ctk.CTkButton(control_frame, text="✕", width=30, fg_color="#444", command=self.cancel_edit)

        # --- FILTERS ---
        filter_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 10))
        
        for cat in ["All", "Health", "Work", "Learning"]:
            btn_color = "#2CC985" if self.current_filter == cat else "transparent"
            text_col = "white" if self.current_filter == cat else "grey"
            ctk.CTkButton(filter_frame, text=cat, width=60, height=25, fg_color=btn_color, 
                          text_color=text_col, corner_radius=20,
                          command=lambda c=cat: self.set_filter(c)).pack(side="left", padx=5)

        # --- HABIT LIST ---
        self.progress = ctk.CTkProgressBar(self.main_area, height=10, corner_radius=8)
        self.progress.pack(fill="x", pady=(0, 15))
        self.progress.set(0)

        self.scroll_frame = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)
        self.load_habits_list()

    def set_filter(self, category):
        self.current_filter = category
        self.show_dashboard()

    def load_habits_list(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        
        habits = self.db.get_habits(self.current_filter)
        total = len(habits)
        done_count = 0

        for (h_id, name, remind_time, category, target, is_done, progress) in habits:
            streak = self.db.get_streak(h_id)
            if is_done: done_count += 1
            disp_time = remind_time if remind_time else ""
            
            HabitCard(
                self.scroll_frame, h_id, name, disp_time, category, target, progress, is_done, streak, 
                self.toggle_habit, 
                self.delete_habit_event, 
                self.start_edit_event
            )
            # Use pack to stack them vertically
            # Accessing the last child added to scroll_frame to pack it
            self.scroll_frame.winfo_children()[-1].pack(fill="x", pady=6)

        if total > 0: self.progress.set(done_count / total)
        else: self.progress.set(0)

    def save_habit_event(self):
        name = self.name_entry.get()
        time_val = self.time_entry.get().strip()
        cat = self.cat_var.get()
        freq_str = self.freq_var.get()
        
        # Convert "3x / Week" to int 3
        if freq_str == "Daily": target = 0
        else: target = int(freq_str[0])

        valid_time = ""
        if time_val:
            try: valid_time = datetime.strptime(time_val, "%H:%M").strftime("%H:%M")
            except: pass

        if name:
            if self.editing_id:
                # Update Existing
                self.db.update_habit(self.editing_id, name, valid_time, cat, target)
                self.cancel_edit()
            else:
                # Add New
                self.db.add_habit(name, valid_time, cat, target)
                self.name_entry.delete(0, "end")
                self.time_entry.delete(0, "end")
            
            self.load_habits_list()

    def start_edit_event(self, h_id, name, time_val, category, target):
        self.editing_id = h_id
        
        # Fill inputs
        self.name_entry.delete(0, "end"); self.name_entry.insert(0, name)
        self.time_entry.delete(0, "end"); 
        if time_val: self.time_entry.insert(0, time_val)
        self.cat_var.set(category)
        
        if target == 0: self.freq_var.set("Daily")
        else: self.freq_var.set(f"{target}x / Week")

        # Change button state
        self.action_btn.configure(text="💾 Save", fg_color="#e67e22", hover_color="#d35400")
        self.cancel_btn.pack(side="left", padx=5)

    def cancel_edit(self):
        self.editing_id = None
        self.name_entry.delete(0, "end")
        self.time_entry.delete(0, "end")
        self.cat_var.set("General")
        self.freq_var.set("Daily")
        self.action_btn.configure(text="+ Add", fg_color="#2CC985", hover_color="#1e8e5e")
        self.cancel_btn.pack_forget()

    def toggle_habit(self, h_id, is_checked):
        self.db.toggle_habit(h_id, is_checked)
        
        if is_checked: 
            self.sound.play_success()
        
        # Recalculate XP and refresh Sidebar immediately
        self.calculate_xp()
        self.refresh_sidebar()
        
        self.load_habits_list()

    def delete_habit_event(self, h_id):
        self.db.delete_habit(h_id)
        if self.editing_id == h_id: self.cancel_edit()
        
        self.calculate_xp()
        self.refresh_sidebar()
        self.load_habits_list()

    def show_analytics(self): 
        self.clear_frame()
        # Initialize the separated Analytics Panel
        analytics_view = AnalyticsPanel(self.main_area, self.db)
        analytics_view.pack(fill="both", expand=True)

    def clear_frame(self):
        for w in self.main_area.winfo_children(): w.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()