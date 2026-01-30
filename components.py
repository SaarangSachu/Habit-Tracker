import customtkinter as ctk

class HabitCard(ctk.CTkFrame):
    def __init__(self, parent, h_id, name, is_done, streak, toggle_callback):
        super().__init__(parent, fg_color="#2b2b2b", corner_radius=15, border_width=1, border_color="#333333")
        self.h_id = h_id
        self.toggle_callback = toggle_callback
        
        # Grid Layout
        self.columnconfigure(0, weight=1) # Name takes all space
        
        # 1. Habit Name
        # If done, we make it green text, else white
        text_color = "#2CC985" if is_done else "white"
        self.name_lbl = ctk.CTkLabel(self, text=name, font=("Segoe UI", 16, "bold"), text_color=text_color, anchor="w")
        self.name_lbl.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        # 2. Streak Badge (Only shows if streak > 0)
        if streak > 0:
            fire_color = "#FF9F1C" if streak > 3 else "#888888" # Orange if on fire
            self.streak_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=1, border_color=fire_color, corner_radius=20, height=25)
            self.streak_frame.grid(row=0, column=1, padx=10)
            
            ctk.CTkLabel(self.streak_frame, text=f"🔥 {streak}", font=("Arial", 12, "bold"), text_color=fire_color).pack(padx=10, pady=2)

        # 3. Modern Checkbox
        self.chk = ctk.CTkCheckBox(
            self, 
            text="", 
            width=28, 
            height=28, 
            corner_radius=8,
            border_color="#2CC985",
            fg_color="#2CC985",
            hover_color="#1e8e5e",
            command=self.on_click
        )
        if is_done: self.chk.select()
        self.chk.grid(row=0, column=2, padx=(0, 20))

    def on_click(self):
        # We pass the ID and the NEW state (1 or 0) back to main.py
        self.toggle_callback(self.h_id, self.chk.get())

class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, nav_callback):
        super().__init__(parent, width=220, corner_radius=0, fg_color="#1a1a1a")
        self.nav_callback = nav_callback
        
        # Logo Area
        self.logo = ctk.CTkLabel(self, text="WINTER ARC", font=("Impact", 28), text_color="#2CC985")
        self.logo.pack(pady=50)

        # Navigation Buttons
        self.create_nav_btn("🏠  Dashboard", "dashboard")
        self.create_nav_btn("📊  Analytics", "analytics")
        
        # Bottom Version Label
        ctk.CTkLabel(self, text="v1.0.0", text_color="grey").pack(side="bottom", pady=20)

    def create_nav_btn(self, text, value):
        btn = ctk.CTkButton(
            self, 
            text=text, 
            fg_color="transparent", 
            text_color="#cccccc",
            hover_color="#333333",
            anchor="w",
            height=40,
            font=("Segoe UI", 16),
            command=lambda: self.nav_callback(value)
        )
        btn.pack(fill="x", padx=10, pady=5)