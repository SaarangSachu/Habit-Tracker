import customtkinter as ctk
from datetime import date, timedelta

# Import our new modules
from database import Database
from components import HabitCard, Sidebar

# App Configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Winter Arc Tracker")
        self.geometry("950x650")
        self.db = Database()
        
        # Grid Layout (Sidebar | Main Content)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. Initialize Sidebar
        self.sidebar = Sidebar(self, self.navigate)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # 2. Main Content Area
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        
        # Load Dashboard by default
        self.show_dashboard()

    def navigate(self, page_name):
        if page_name == "dashboard":
            self.show_dashboard()
        elif page_name == "analytics":
            self.show_analytics()

    def show_dashboard(self):
        self.clear_frame()
        
        # Title Header
        header_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="Today's Focus", font=("Segoe UI", 32, "bold")).pack(side="left")
        
        # Add Button Logic
        self.add_entry = ctk.CTkEntry(header_frame, placeholder_text="New Habit...", width=200, height=35)
        self.add_entry.pack(side="right", padx=10)
        ctk.CTkButton(header_frame, text="+ Add", width=80, height=35, command=self.add_habit_event).pack(side="right")

        # Progress Bar
        self.progress = ctk.CTkProgressBar(self.main_area, height=15, corner_radius=8)
        self.progress.pack(fill="x", pady=(0, 25))
        self.progress.set(0) # Default

        # Scrollable Habit List
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)
        
        self.load_habits_list()

    def load_habits_list(self):
        # Clear list
        for widget in self.scroll_frame.winfo_children(): widget.destroy()

        habits = self.db.get_habits()
        total = len(habits)
        done_count = 0

        for (h_id, name, is_done) in habits:
            streak = self.db.get_streak(h_id)
            if is_done: done_count += 1
            
            # Create the custom Card Component
            card = HabitCard(self.scroll_frame, h_id, name, is_done, streak, self.toggle_habit)
            card.pack(fill="x", pady=8)

        # Update Progress Bar
        if total > 0:
            self.progress.set(done_count / total)
        else:
            self.progress.set(0)

    def toggle_habit(self, h_id, is_checked):
        self.db.toggle_habit(h_id, is_checked)
        self.load_habits_list() # Reload UI to update progress bar and colors

    def add_habit_event(self):
        text = self.add_entry.get()
        if text:
            self.db.add_habit(text)
            self.show_dashboard()

    def show_analytics(self):
        self.clear_frame()
        ctk.CTkLabel(self.main_area, text="Activity Heatmap", font=("Segoe UI", 32, "bold")).pack(anchor="w", pady=(0, 30))
        
        heatmap_frame = ctk.CTkFrame(self.main_area, fg_color="#1a1a1a", corner_radius=15)
        heatmap_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Center the grid
        grid = ctk.CTkFrame(heatmap_frame, fg_color="transparent")
        grid.place(relx=0.5, rely=0.5, anchor="center")
        
        data = self.db.get_activity_data()
        start = date.today() - timedelta(days=27)

        for i in range(28):
            day = start + timedelta(days=i)
            count = data.get(str(day), 0)
            
            if count == 0: color = "#2d2d2d"
            elif count <= 2: color = "#1e7e48"
            else: color = "#2CC985" # Bright Green
            
            box = ctk.CTkFrame(grid, width=50, height=50, fg_color=color, corner_radius=4)
            box.grid(row=i//7, column=i%7, padx=6, pady=6)
            
            # Date label inside box
            ctk.CTkLabel(box, text=str(day.day), font=("Arial", 10), text_color="white").place(relx=0.5, rely=0.5, anchor="center")

    def clear_frame(self):
        for widget in self.main_area.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()