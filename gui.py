import customtkinter as ctk
import mysql.connector
import os
from datetime import date, timedelta
from dotenv import load_dotenv

# --- 1. CONFIGURATION ---
load_dotenv()
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

# --- 2. DATABASE CLASS (Updated with Analytics) ---
class Database:
    def get_connection(self):
        return mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            database=os.getenv('DB_NAME')
        )

    def get_habits(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        query = """
        SELECT h.habit_id, h.habit_name, 
               CASE WHEN d.log_id IS NOT NULL THEN 1 ELSE 0 END as is_done
        FROM habits h
        LEFT JOIN daily_logs d ON h.habit_id = d.habit_id AND d.log_date = CURDATE()
        """
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        return result

    def toggle_habit(self, habit_id, is_checked):
        conn = self.get_connection()
        cursor = conn.cursor()
        if is_checked:
            cursor.execute("INSERT IGNORE INTO daily_logs (habit_id, log_date) VALUES (%s, CURDATE())", (habit_id,))
        else:
            cursor.execute("DELETE FROM daily_logs WHERE habit_id = %s AND log_date = CURDATE()", (habit_id,))
        conn.commit()
        conn.close()

    def add_habit(self, name):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO habits (habit_name) VALUES (%s)", (name,))
        conn.commit()
        conn.close()

    # --- NEW FEATURE: STREAK CALCULATION ---
    def get_streak(self, habit_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Get all unique dates this habit was completed, ordered by latest
        cursor.execute("""
            SELECT DISTINCT log_date FROM daily_logs 
            WHERE habit_id = %s ORDER BY log_date DESC
        """, (habit_id,))
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not dates:
            return 0

        streak = 0
        current_check = date.today()
        
        # Check if today is done; if not, check if yesterday was done (streak lives 1 day)
        if current_check in dates:
            streak += 1
            current_check -= timedelta(days=1)
        elif (current_check - timedelta(days=1)) in dates:
            current_check -= timedelta(days=1)
        else:
            return 0 # Streak broken

        # Count backwards
        for d in dates:
            if d == current_check:
                # We already counted the first day above if it was today
                if d != date.today(): 
                    streak += 1
                current_check -= timedelta(days=1)
        
        return streak

    # --- NEW FEATURE: HEATMAP DATA ---
    def get_activity_data(self):
        # Returns a dictionary: { '2023-10-27': 5_habits_done }
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT log_date, COUNT(*) FROM daily_logs GROUP BY log_date")
        data = {str(row[0]): row[1] for row in cursor.fetchall()}
        conn.close()
        return data

db = Database()

# --- 3. STATS WINDOW (The Heatmap) ---
class StatsWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("400x450")
        self.title("Consistency Heatmap")
        self.resizable(False, False)

        label = ctk.CTkLabel(self, text="LAST 28 DAYS ACTIVITY", font=("Roboto", 16, "bold"), text_color="#2CC985")
        label.pack(pady=20)

        # The Grid Container
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(pady=10)

        self.render_heatmap()

    def render_heatmap(self):
        activity_data = db.get_activity_data()
        today = date.today()
        
        # Grid: 4 rows (weeks) x 7 columns (days)
        # We want to show the LAST 28 days
        start_date = today - timedelta(days=27)

        for i in range(28):
            current_day = start_date + timedelta(days=i)
            day_str = str(current_day)
            
            # Get count (0 if no data)
            count = activity_data.get(day_str, 0)
            
            # Determine Color Intensity
            if count == 0:
                color = "#2b2b2b" # Grey (Empty)
            elif count == 1:
                color = "#124429" # Very Dark Green
            elif count <= 3:
                color = "#1e7e48" # Medium Green
            else:
                color = "#2CC985" # Bright Green (High Activity)

            # Create the Square
            box = ctk.CTkFrame(
                self.grid_frame, 
                width=40, 
                height=40, 
                fg_color=color,
                corner_radius=4
            )
            # Grid math: Row is i // 7, Column is i % 7
            box.grid(row=i//7, column=i%7, padx=3, pady=3)
            
            # Add Tooltip (Using a simple label inside for the date)
            # Only show Day number (e.g., "30")
            day_label = ctk.CTkLabel(box, text=str(current_day.day), font=("Arial", 10), text_color="white")
            day_label.place(relx=0.5, rely=0.5, anchor="center")

# --- 4. MAIN APP ---
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Winter Arc Tracker")
        self.geometry("450x700")
        self.resizable(False, False)

        # Header
        self.header = ctk.CTkLabel(self, text="MY ROUTINE", font=("Roboto", 24, "bold"), text_color="#2CC985")
        self.header.pack(pady=20)

        # Stats Button (New)
        self.stats_btn = ctk.CTkButton(self, text="View Heatmap 📊", command=self.open_stats, width=150, fg_color="#3B3B3B")
        self.stats_btn.pack(pady=(0, 20))

        # Scrollable Frame
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=380, height=450)
        self.scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Add Habit Section
        self.entry = ctk.CTkEntry(self, placeholder_text="New Habit Name...", width=250)
        self.entry.pack(side="left", padx=(20, 10), pady=20)
        
        self.add_btn = ctk.CTkButton(self, text="Add", width=80, command=self.add_habit_event)
        self.add_btn.pack(side="left", pady=20)

        self.load_habits()

    def open_stats(self):
        stats_window = StatsWindow(self)
        stats_window.grab_set() # Focus on this window

    def load_habits(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        habits = db.get_habits()

        if not habits:
            label = ctk.CTkLabel(self.scroll_frame, text="No habits yet.", text_color="gray")
            label.pack(pady=20)

        for (h_id, name, is_done) in habits:
            # 1. Get Streak
            streak = db.get_streak(h_id)
            
            # 2. Format Text: "Gym 🔥 5"
            streak_text = f" 🔥 {streak}" if streak > 0 else ""
            display_text = f"{name}{streak_text}"

            # 3. Create Checkbox
            chk = ctk.CTkCheckBox(
                self.scroll_frame, 
                text=display_text, 
                font=("Roboto", 16),
            )
            if is_done:
                chk.select()
            
            chk.habit_id = h_id
            chk.configure(command=lambda c=chk: self.checkbox_clicked(c))
            chk.pack(pady=10, padx=10, anchor="w")

    def checkbox_clicked(self, checkbox_widget):
        h_id = checkbox_widget.habit_id
        is_checked = checkbox_widget.get() 
        db.toggle_habit(h_id, is_checked)
        
        # Reload to update the Streak counter immediately
        self.load_habits()

    def add_habit_event(self):
        text = self.entry.get()
        if text:
            db.add_habit(text)
            self.entry.delete(0, "end")
            self.load_habits()

if __name__ == "__main__":
    app = App()
    app.mainloop()