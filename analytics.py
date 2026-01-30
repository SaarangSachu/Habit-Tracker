import customtkinter as ctk
from datetime import date, timedelta

class AnalyticsPanel(ctk.CTkFrame):
    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        
        # 1. Main Title
        ctk.CTkLabel(self, text="Performance Analytics", font=("Segoe UI", 32, "bold")).pack(anchor="w", pady=(0, 20))

        # 2. KPI Cards (Key Performance Indicators)
        self.create_kpi_row()

        # 3. Heatmap Section
        ctk.CTkLabel(self, text="Consistency Heatmap (Last 30 Days)", font=("Segoe UI", 20, "bold"), text_color="#aaaaaa").pack(anchor="w", pady=(30, 10))
        self.create_heatmap()

    def create_kpi_row(self):
        # Container for cards
        kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=10)

        # Fetch Data
        total_done = self.db.get_total_completions()
        total_xp = total_done * 10
        
        # Card 1: Total XP
        self.create_card(kpi_frame, "Total XP", f"{total_xp}", "⚡", "#e67e22")
        
        # Card 2: Habits Crushed
        self.create_card(kpi_frame, "Habits Crushed", f"{total_done}", "✅", "#2CC985")
        
        # Card 3: Completion Rate (Today)
        # Calculate today's percentage
        habits = self.db.get_habits()
        if habits:
            done_today = sum(1 for h in habits if h[5] == 1) # Index 5 is is_done
            total_today = len(habits)
            rate = int((done_today / total_today) * 100)
        else:
            rate = 0
            
        self.create_card(kpi_frame, "Today's Efficiency", f"{rate}%", "📈", "#3498db")

    def create_card(self, parent, title, value, icon, color):
        card = ctk.CTkFrame(parent, fg_color="#2b2b2b", corner_radius=15, border_width=1, border_color="#444")
        card.pack(side="left", expand=True, fill="both", padx=5)
        
        # Content
        ctk.CTkLabel(card, text=icon, font=("Arial", 30)).pack(pady=(15, 0))
        ctk.CTkLabel(card, text=value, font=("Segoe UI", 28, "bold"), text_color=color).pack()
        ctk.CTkLabel(card, text=title, font=("Arial", 12), text_color="#aaaaaa").pack(pady=(0, 15))

    def create_heatmap(self):
        heatmap_frame = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=15)
        heatmap_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        grid_container = ctk.CTkFrame(heatmap_frame, fg_color="transparent")
        grid_container.place(relx=0.5, rely=0.5, anchor="center")

        data = self.db.get_activity_data()
        
        today = date.today()
        start_date = today - timedelta(days=27)
        
        for i in range(28):
            target_date = start_date + timedelta(days=i)
            date_str = str(target_date)
            count = data.get(date_str, 0)
            
            # --- FIX IS HERE ---
            if count == 0: bg = "#2d2d2d"       # Changed == to =
            elif count <= 2: bg = "#0e4429"
            elif count <= 4: bg = "#006d32"
            elif count <= 6: bg = "#26a641"
            else: bg = "#39d353"
            
            box = ctk.CTkFrame(grid_container, width=50, height=50, fg_color=bg, corner_radius=4)
            box.grid(row=i//7, column=i%7, padx=6, pady=6)
            
            day_num = target_date.day
            text_col = "#aaafff" if count > 0 else "#555"
            ctk.CTkLabel(box, text=str(day_num), text_color=text_col, font=("Arial", 10)).place(relx=0.5, rely=0.5, anchor="center")