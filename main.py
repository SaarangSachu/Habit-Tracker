import customtkinter as ctk
import threading
import time
from plyer import notification
from datetime import datetime

from database import Database
from components import HabitCard, Sidebar
from clock_widget import RealTimeClock 
from sounds import SoundManager

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Winter Arc Tracker v2")
        self.geometry("1000x700")
        self.db = Database()
        self.sound = SoundManager()
        
        self.editing_id = None # Tracks if we are editing a habit

        # Background Thread
        self.stop_thread = False
        self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.thread.start()

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.sidebar = Sidebar(self, self.navigate)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        
        # State for filtering
        self.current_filter = "All"
        self.show_dashboard()

    def run_scheduler(self):
        while not self.stop_thread:
            current_time = datetime.now().strftime("%H:%M")
            try:
                # Scheduler ignores category filter, it checks EVERYTHING
                habits = self.db.get_habits(category_filter="All")
                for (h_id, name, remind_time, cat, is_done) in habits:
                    if remind_time and not is_done:
                        if remind_time == current_time:
                            self.sound.play_notification()
                            notification.notify(title="Time to Grind!", message=f"{name}", timeout=10)
                            time.sleep(60)
            except: pass
            time.sleep(10)

    def navigate(self, page):
        if page == "dashboard": self.show_dashboard()
        elif page == "analytics": self.show_analytics()

    def show_dashboard(self):
        self.clear_frame()
        
        # --- HEADER (Title + Clock) ---
        header_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header_frame, text="Today's Focus", font=("Segoe UI", 32, "bold")).pack(side="left")
        RealTimeClock(header_frame).pack(side="left", padx=20)

        # --- CONTROLS ROW (Add/Edit Inputs) ---
        control_frame = ctk.CTkFrame(self.main_area, fg_color="#2b2b2b", corner_radius=10)
        control_frame.pack(fill="x", pady=(0, 20), ipady=5)

        # Inputs
        self.name_entry = ctk.CTkEntry(control_frame, placeholder_text="Habit Name...", width=250)
        self.name_entry.pack(side="left", padx=10, pady=10)
        
        self.time_entry = ctk.CTkEntry(control_frame, placeholder_text="09:00", width=80)
        self.time_entry.pack(side="left", padx=5)
        
        # Category Dropdown
        self.cat_var = ctk.StringVar(value="General")
        self.cat_menu = ctk.CTkComboBox(control_frame, values=["General", "Health", "Work", "Learning"], 
                                        variable=self.cat_var, width=110, state="readonly")
        self.cat_menu.pack(side="left", padx=5)

        # Action Button (Dynamic Text: Add vs Update)
        self.action_btn = ctk.CTkButton(control_frame, text="+ Add Task", width=100, command=self.save_habit_event)
        self.action_btn.pack(side="left", padx=10)
        
        # Cancel Edit Button (Hidden by default)
        self.cancel_btn = ctk.CTkButton(control_frame, text="✕", width=30, fg_color="#444", command=self.cancel_edit)
        
        # --- FILTER TABS ---
        filter_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 10))
        
        categories = ["All", "Health", "Work", "Learning"]
        for cat in categories:
            btn_color = "#2CC985" if self.current_filter == cat else "transparent"
            text_col = "white" if self.current_filter == cat else "grey"
            ctk.CTkButton(filter_frame, text=cat, width=60, height=25, fg_color=btn_color, 
                          text_color=text_col, corner_radius=20,
                          command=lambda c=cat: self.set_filter(c)).pack(side="left", padx=5)

        # --- PROGRESS & LIST ---
        self.progress = ctk.CTkProgressBar(self.main_area, height=10, corner_radius=8)
        self.progress.pack(fill="x", pady=(0, 15))
        self.progress.set(0)

        self.scroll_frame = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)
        self.load_habits_list()

    def set_filter(self, category):
        self.current_filter = category
        self.show_dashboard() # Reload UI with new filter

    def load_habits_list(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        
        # Pass filter to DB
        habits = self.db.get_habits(self.current_filter)
        total = len(habits)
        done_count = 0

        for (h_id, name, remind_time, category, is_done) in habits:
            streak = self.db.get_streak(h_id)
            if is_done: done_count += 1
            disp_time = remind_time if remind_time else ""
            
            HabitCard(self.scroll_frame, h_id, name, disp_time, category, is_done, streak, 
                      self.toggle_habit, self.delete_habit_event, self.start_edit_event).pack(fill="x", pady=6)

        if total > 0: self.progress.set(done_count / total)
        else: self.progress.set(0)

    # --- ACTIONS ---
    def save_habit_event(self):
        name = self.name_entry.get()
        time_val = self.time_entry.get().strip()
        cat = self.cat_var.get()
        
        # Time Validation
        valid_time = ""
        if time_val:
            try: valid_time = datetime.strptime(time_val, "%H:%M").strftime("%H:%M")
            except: pass

        if name:
            if self.editing_id:
                # UPDATE EXISTING
                self.db.update_habit(self.editing_id, name, valid_time, cat)
                self.cancel_edit() # Reset mode
            else:
                # ADD NEW
                self.db.add_habit(name, valid_time, cat)
                self.name_entry.delete(0, "end")
                self.time_entry.delete(0, "end")
            
            self.load_habits_list()

    def start_edit_event(self, h_id, name, time_val, category):
        # Enter Edit Mode
        self.editing_id = h_id
        
        # 1. Fill inputs with existing data
        self.name_entry.delete(0, "end"); self.name_entry.insert(0, name)
        self.time_entry.delete(0, "end"); 
        if time_val: self.time_entry.insert(0, time_val)
        self.cat_var.set(category)
        
        # 2. Change Button Style
        self.action_btn.configure(text="💾 Save", fg_color="#e67e22", hover_color="#d35400")
        self.cancel_btn.pack(side="left", padx=5) # Show cancel button

    def cancel_edit(self):
        # Reset to default "Add Mode"
        self.editing_id = None
        self.name_entry.delete(0, "end")
        self.time_entry.delete(0, "end")
        self.cat_var.set("General")
        self.action_btn.configure(text="+ Add Task", fg_color="#2CC985", hover_color="#1e8e5e")
        self.cancel_btn.pack_forget() # Hide cancel button

    def toggle_habit(self, h_id, is_checked):
        self.db.toggle_habit(h_id, is_checked)
        if is_checked: self.sound.play_success()
        self.load_habits_list()

    def delete_habit_event(self, h_id):
        self.db.delete_habit(h_id)
        if self.editing_id == h_id: self.cancel_edit() # Cancel edit if deleting that item
        self.load_habits_list()

    def show_analytics(self): 
        # (Same analytics logic)
        self.clear_frame()
        # ... (Your analytics code goes here)

    def clear_frame(self):
        for w in self.main_area.winfo_children(): w.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()