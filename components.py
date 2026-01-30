import customtkinter as ctk

class HabitCard(ctk.CTkFrame):
    def __init__(self, parent, h_id, name, time, category, target, progress, is_done, streak, toggle_callback, delete_callback, edit_callback):
        
        # Color Logic
        border_col = "#333333"
        if category == "Health": border_col = "#3498db"
        elif category == "Work": border_col = "#e74c3c"
        elif category == "Learning": border_col = "#2ecc71"
        
        super().__init__(parent, fg_color="#2b2b2b", corner_radius=15, border_width=2, border_color=border_col)
        
        self.h_id = h_id
        self.toggle_callback = toggle_callback
        self.delete_callback = delete_callback
        self.edit_callback = edit_callback
        
        # Store data for editing later
        self.name = name
        self.time = time
        self.category = category
        self.target = target
        
        self.columnconfigure(0, weight=1)
        
        # --- ROW 1: Info ---
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")
        
        # Name
        text_color = "#2CC985" if is_done else "white"
        ctk.CTkLabel(info_frame, text=name, font=("Segoe UI", 16, "bold"), text_color=text_color).pack(side="left")
        
        # Category Tag
        ctk.CTkLabel(info_frame, text=category.upper(), font=("Arial", 9, "bold"), text_color=border_col).pack(side="left", padx=8)

        # Time
        if time:
            ctk.CTkLabel(info_frame, text=f"⏰ {time}", font=("Arial", 12), text_color="grey").pack(side="left")

        # --- ROW 2: Weekly Progress (Only if target > 0) ---
        if target > 0:
            prog_frame = ctk.CTkFrame(self, fg_color="transparent", height=10)
            prog_frame.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
            
            # Text: "2 / 3 this week"
            status_col = "#2CC985" if progress >= target else "#aaaaaa"
            ctk.CTkLabel(prog_frame, text=f"Weekly Goal: {progress}/{target}", font=("Arial", 10), text_color=status_col).pack(side="left")
            
            # Mini Bar
            bar = ctk.CTkProgressBar(prog_frame, width=100, height=6, progress_color=status_col)
            bar.pack(side="right")
            percent = progress / target if target > 0 else 0
            if percent > 1: percent = 1
            bar.set(percent)

        # Streak Badge (Right Side)
        if streak > 0:
            fire_col = "#FF9F1C" if streak > 3 else "#888888"
            self.streak_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=1, border_color=fire_col, corner_radius=20, height=25)
            self.streak_frame.grid(row=0, column=1, padx=5)
            ctk.CTkLabel(self.streak_frame, text=f"🔥 {streak}", font=("Arial", 12, "bold"), text_color=fire_col).pack(padx=8, pady=2)

        # Checkbox
        self.chk = ctk.CTkCheckBox(self, text="", width=24, height=24, corner_radius=8, 
                                   border_color="#2CC985", fg_color="#2CC985", hover_color="#1e8e5e", command=self.on_toggle)
        if is_done: self.chk.select()
        self.chk.grid(row=0, column=2, padx=(0, 10))

        # Edit
        ctk.CTkButton(self, text="✏️", width=30, height=30, fg_color="transparent", hover_color="#333333", command=self.on_edit).grid(row=0, column=3, padx=(0, 5))
        
        # Delete
        ctk.CTkButton(self, text="🗑️", width=30, height=30, fg_color="transparent", hover_color="#c0392b", command=self.on_delete).grid(row=0, column=4, padx=(0, 15))

    def on_toggle(self): self.toggle_callback(self.h_id, self.chk.get())
    def on_delete(self): self.delete_callback(self.h_id)
    def on_edit(self): self.edit_callback(self.h_id, self.name, self.time, self.category, self.target)

class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, nav_callback):
        super().__init__(parent, width=220, corner_radius=0, fg_color="#1a1a1a")
        self.nav_callback = nav_callback
        ctk.CTkLabel(self, text="WINTER ARC", font=("Impact", 28), text_color="#2CC985").pack(pady=50)
        self.create_nav_btn("🏠  Dashboard", "dashboard")
        self.create_nav_btn("📊  Analytics", "analytics")
        ctk.CTkLabel(self, text="v2.1 Weekly Goals", text_color="grey").pack(side="bottom", pady=20)

    def create_nav_btn(self, text, value):
        ctk.CTkButton(self, text=text, fg_color="transparent", text_color="#cccccc", hover_color="#333333", anchor="w", height=40, font=("Segoe UI", 16), command=lambda: self.nav_callback(value)).pack(fill="x", padx=10, pady=5)