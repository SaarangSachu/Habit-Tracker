import customtkinter as ctk

class HabitCard(ctk.CTkFrame):
    # UPDATED: Now accepts 'delete_callback'
    def __init__(self, parent, h_id, name, time, is_done, streak, toggle_callback, delete_callback):
        super().__init__(parent, fg_color="#2b2b2b", corner_radius=15, border_width=1, border_color="#333333")
        self.h_id = h_id
        self.toggle_callback = toggle_callback
        self.delete_callback = delete_callback
        
        self.columnconfigure(0, weight=1)
        
        # 1. Name and Time
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        
        text_color = "#2CC985" if is_done else "white"
        self.name_lbl = ctk.CTkLabel(info_frame, text=name, font=("Segoe UI", 16, "bold"), text_color=text_color, anchor="w")
        self.name_lbl.pack(side="left")
        
        if time:
            self.time_lbl = ctk.CTkLabel(info_frame, text=f"⏰ {time}", font=("Arial", 12), text_color="grey")
            self.time_lbl.pack(side="left", padx=10)

        # 2. Streak Badge
        if streak > 0:
            fire_color = "#FF9F1C" if streak > 3 else "#888888"
            self.streak_frame = ctk.CTkFrame(self, fg_color="transparent", border_width=1, border_color=fire_color, corner_radius=20, height=25)
            self.streak_frame.grid(row=0, column=1, padx=10)
            ctk.CTkLabel(self.streak_frame, text=f"🔥 {streak}", font=("Arial", 12, "bold"), text_color=fire_color).pack(padx=10, pady=2)

        # 3. Checkbox
        self.chk = ctk.CTkCheckBox(
            self, text="", width=28, height=28, corner_radius=8,
            border_color="#2CC985", fg_color="#2CC985", hover_color="#1e8e5e",
            command=self.on_toggle
        )
        if is_done: self.chk.select()
        self.chk.grid(row=0, column=2, padx=(0, 10))

        # 4. NEW: Delete Button (Trash Icon)
        self.del_btn = ctk.CTkButton(
            self, 
            text="🗑️", 
            width=30, 
            height=30, 
            fg_color="transparent", 
            hover_color="#c0392b", # Red on hover
            text_color="#555555",
            command=self.on_delete
        )
        self.del_btn.grid(row=0, column=3, padx=(0, 15))

    def on_toggle(self):
        self.toggle_callback(self.h_id, self.chk.get())

    def on_delete(self):
        # Trigger the delete callback
        self.delete_callback(self.h_id)

# Sidebar class remains the same...
class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, nav_callback):
        super().__init__(parent, width=220, corner_radius=0, fg_color="#1a1a1a")
        self.nav_callback = nav_callback
        self.logo = ctk.CTkLabel(self, text="WINTER ARC", font=("Impact", 28), text_color="#2CC985")
        self.logo.pack(pady=50)
        self.create_nav_btn("🏠  Dashboard", "dashboard")
        self.create_nav_btn("📊  Analytics", "analytics")
        ctk.CTkLabel(self, text="v1.2.0", text_color="grey").pack(side="bottom", pady=20)

    def create_nav_btn(self, text, value):
        btn = ctk.CTkButton(
            self, text=text, fg_color="transparent", text_color="#cccccc",
            hover_color="#333333", anchor="w", height=40, font=("Segoe UI", 16),
            command=lambda: self.nav_callback(value)
        )
        btn.pack(fill="x", padx=10, pady=5)