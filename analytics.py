import customtkinter as ctk
from datetime import date, timedelta

class AnalyticsPanel(ctk.CTkFrame):
    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        
        ctk.CTkLabel(self.scroll, text="Analytics Dashboard", font=("Segoe UI", 32, "bold")).pack(anchor="w", pady=(0, 20))

        # KPI Cards
        self.create_kpi_row()

        # Heatmap
        ctk.CTkLabel(self.scroll, text="Consistency Heatmap (30 Days)", font=("Segoe UI", 20, "bold"), text_color="#aaaaaa").pack(anchor="w", pady=(30, 10))
        self.create_heatmap()

        # Distribution Chart
        ctk.CTkLabel(self.scroll, text="Habit Distribution (Planned)", font=("Segoe UI", 20, "bold"), text_color="#aaaaaa").pack(anchor="w", pady=(30, 10))
        self.create_category_distribution()

    def create_kpi_row(self):
        kpi_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=10)

        total_done = self.db.get_total_completions()
        total_xp = total_done * 10
        habits = self.db.get_habits()
        if habits:
            done_today = sum(1 for h in habits if h[5] == 1)
            total_today = len(habits)
            rate = int((done_today / total_today) * 100)
        else:
            rate = 0
            
        self.create_card(kpi_frame, "Total XP", f"{total_xp}", "⚡", "#e67e22")
        self.create_card(kpi_frame, "Habits Done", f"{total_done}", "✅", "#2CC985")
        self.create_card(kpi_frame, "Efficiency", f"{rate}%", "📈", "#3498db")

    def create_card(self, parent, title, value, icon, color):
        card = ctk.CTkFrame(parent, fg_color="#2b2b2b", corner_radius=15, border_width=1, border_color="#444")
        card.pack(side="left", expand=True, fill="both", padx=5)
        ctk.CTkLabel(card, text=icon, font=("Arial", 30)).pack(pady=(15, 0))
        ctk.CTkLabel(card, text=value, font=("Segoe UI", 28, "bold"), text_color=color).pack()
        ctk.CTkLabel(card, text=title, font=("Arial", 12), text_color="#aaaaaa").pack(pady=(0, 15))

    def create_heatmap(self):
        heatmap_frame = ctk.CTkFrame(self.scroll, fg_color="#1a1a1a", corner_radius=15)
        heatmap_frame.pack(fill="x", padx=0, pady=0)
        grid = ctk.CTkFrame(heatmap_frame, fg_color="transparent")
        grid.pack(pady=15)

        data = self.db.get_activity_data()
        today = date.today()
        start_date = today - timedelta(days=27)
        
        for i in range(28):
            target_date = start_date + timedelta(days=i)
            date_str = str(target_date)
            count = data.get(date_str, 0)
            
            # Determine Color
            if count == 0: bg = "#2d2d2d"
            elif count <= 2: bg = "#0e4429"
            elif count <= 4: bg = "#006d32"
            else: bg = "#39d353"
            
            # Create the Box
            box = ctk.CTkFrame(grid, width=40, height=40, fg_color=bg, corner_radius=4)
            box.grid(row=i//7, column=i%7, padx=4, pady=4)

            # --- FIX IS HERE: Add the Day Number Label ---
            day_num = target_date.day
            text_col = "#e0e0e0" if count > 0 else "#555555" # Lighter text if active, dark if empty
            
            # We use .place() to center the text perfectly inside the box
            label = ctk.CTkLabel(box, text=str(day_num), text_color=text_col, font=("Arial", 10, "bold"))
            label.place(relx=0.5, rely=0.5, anchor="center")

    def create_category_distribution(self):
        chart_frame = ctk.CTkFrame(self.scroll, fg_color="#2b2b2b", corner_radius=15)
        chart_frame.pack(fill="x", pady=(0, 20))
        dist_data = self.db.get_category_distribution()
        total = sum(d['count'] for d in dist_data.values())
        
        if total == 0:
            ctk.CTkLabel(chart_frame, text="No habits yet!", text_color="grey").pack(pady=20)
            return

        for cat_name, data in dist_data.items():
            count = data['count']
            color = data['color']
            pct = count / total
            row = ctk.CTkFrame(chart_frame, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=10)
            ctk.CTkLabel(row, text=f"{cat_name} ({count})", width=120, anchor="w").pack(side="left")
            progress = ctk.CTkProgressBar(row, progress_color=color, fg_color="#444", height=15)
            progress.pack(side="left", fill="x", expand=True, padx=10)
            progress.set(pct)
            ctk.CTkLabel(row, text=f"{int(pct*100)}%", width=40).pack(side="left")

# --- Performance Page Class ---
class PerformancePanel(ctk.CTkFrame):
    def __init__(self, parent, db):
        super().__init__(parent, fg_color="transparent")
        self.db = db
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        
        ctk.CTkLabel(self.scroll, text="Performance Tracker", font=("Segoe UI", 32, "bold")).pack(anchor="w", pady=(0, 20))
        ctk.CTkLabel(self.scroll, text="Completion Rate (Today)", font=("Segoe UI", 20, "bold"), text_color="#aaaaaa").pack(anchor="w", pady=(20, 10))
        self.create_performance_chart()

    def create_performance_chart(self):
        chart_frame = ctk.CTkFrame(self.scroll, fg_color="#2b2b2b", corner_radius=15)
        chart_frame.pack(fill="x", pady=(0, 20))
        
        perf_data = self.db.get_category_performance()
        if not perf_data:
            ctk.CTkLabel(chart_frame, text="No habits active today.", text_color="grey").pack(pady=20)
            return

        for cat_name, data in perf_data.items():
            total = data['total']
            done = data['done']
            color = data['color']
            pct = done / total if total > 0 else 0
            
            row = ctk.CTkFrame(chart_frame, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=10)
            
            ctk.CTkLabel(row, text=f"{cat_name} ({done}/{total})", width=120, anchor="w", font=("Arial", 12, "bold")).pack(side="left")
            progress = ctk.CTkProgressBar(row, progress_color=color, fg_color="#444", height=15)
            progress.pack(side="left", fill="x", expand=True, padx=10)
            progress.set(pct)
            ctk.CTkLabel(row, text=f"{int(pct*100)}%", width=40, anchor="e", text_color="grey").pack(side="left")