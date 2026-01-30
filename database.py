import sqlite3
import os
from datetime import date, timedelta, datetime

class Database:
    def __init__(self):
        self.db_name = "habits.db"
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # 1. Habits Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                habit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_name TEXT NOT NULL,
                reminder_time TEXT,
                category TEXT DEFAULT 'General',
                weekly_target INTEGER DEFAULT 0
            )
        """)
        
        # 2. Logs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER,
                log_date TEXT,
                FOREIGN KEY(habit_id) REFERENCES habits(habit_id) ON DELETE CASCADE
            )
        """)

        # 3. NEW: Categories Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                cat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                color TEXT
            )
        """)
        
        # Seed Default Categories if empty
        cursor.execute("SELECT count(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            defaults = [
                ("General", "#888888"),
                ("Health", "#3498db"),   # Blue
                ("Work", "#e74c3c"),     # Red
                ("Learning", "#2ecc71"), # Green
                ("Creative", "#9b59b6")  # Purple
            ]
            cursor.executemany("INSERT INTO categories (name, color) VALUES (?, ?)", defaults)

        conn.commit()
        conn.close()

    # --- CATEGORY FUNCTIONS ---
    def get_all_categories(self):
        """Returns list of (name, color) tuples"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, color FROM categories")
        results = cursor.fetchall()
        conn.close()
        return results

    # --- UPDATED CATEGORY FUNCTIONS ---
    def get_all_categories(self):
        """Returns list of (id, name, color) tuples"""
        conn = self.get_connection()
        cursor = conn.cursor()
        # CHANGED: Now fetching cat_id too
        cursor.execute("SELECT cat_id, name, color FROM categories")
        results = cursor.fetchall()
        conn.close()
        return results

    def update_category(self, cat_id, new_name, new_color):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE categories SET name=?, color=? WHERE cat_id=?", 
                           (new_name, new_color, cat_id))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    def get_category_distribution(self):
        """Returns data for the graph: { 'Health': {'count': 5, 'color': '#3498db'}, ... }"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get counts per category
        cursor.execute("SELECT category, COUNT(*) FROM habits GROUP BY category")
        counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get colors
        cursor.execute("SELECT name, color FROM categories")
        colors = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Combine
        data = {}
        for cat, count in counts.items():
            # Default to grey if category color not found
            color = colors.get(cat, "#888888") 
            data[cat] = {"count": count, "color": color}
            
        conn.close()
        return data

    # --- EXISTING FUNCTIONS (Kept same) ---
    def get_habits(self, category_filter=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT h.habit_id, h.habit_name, h.reminder_time, h.category, h.weekly_target,
               CASE WHEN d.log_id IS NOT NULL THEN 1 ELSE 0 END as is_done_today,
               (SELECT COUNT(*) FROM daily_logs dl 
                WHERE dl.habit_id = h.habit_id 
                AND strftime('%Y-%W', dl.log_date) = strftime('%Y-%W', 'now', 'localtime')) as weekly_progress
        FROM habits h
        LEFT JOIN daily_logs d ON h.habit_id = d.habit_id AND d.log_date = date('now', 'localtime')
        """
        
        params = []
        if category_filter and category_filter != "All":
            query += " WHERE h.category = ?"
            params.append(category_filter)
            
        cursor.execute(query, params)
        result = cursor.fetchall()
        conn.close()
        return result

    def add_habit(self, name, time_str, category, target):
        conn = self.get_connection()
        cursor = conn.cursor()
        if time_str == "": time_str = None
        cursor.execute("INSERT INTO habits (habit_name, reminder_time, category, weekly_target) VALUES (?, ?, ?, ?)", 
                       (name, time_str, category, target))
        conn.commit()
        conn.close()

    def update_habit(self, habit_id, name, time_str, category, target):
        conn = self.get_connection()
        cursor = conn.cursor()
        if time_str == "": time_str = None
        cursor.execute("UPDATE habits SET habit_name=?, reminder_time=?, category=?, weekly_target=? WHERE habit_id=?", 
                       (name, time_str, category, target, habit_id))
        conn.commit()
        conn.close()

    def delete_habit(self, habit_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM daily_logs WHERE habit_id = ?", (habit_id,))
        cursor.execute("DELETE FROM habits WHERE habit_id = ?", (habit_id,))
        conn.commit()
        conn.close()

    def toggle_habit(self, habit_id, is_checked):
        conn = self.get_connection()
        cursor = conn.cursor()
        if is_checked:
            cursor.execute("INSERT OR IGNORE INTO daily_logs (habit_id, log_date) VALUES (?, date('now', 'localtime'))", (habit_id,))
        else:
            cursor.execute("DELETE FROM daily_logs WHERE habit_id = ? AND log_date = date('now', 'localtime')", (habit_id,))
        conn.commit()
        conn.close()

    def get_streak(self, habit_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT log_date FROM daily_logs WHERE habit_id = ? ORDER BY log_date DESC", (habit_id,))
        dates_str = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        dates = []
        for d_str in dates_str:
            try: dates.append(datetime.strptime(d_str, "%Y-%m-%d").date())
            except: pass
            
        if not dates: return 0
        
        streak = 0
        current = date.today()
        
        today_str = current.strftime("%Y-%m-%d")
        if today_str in dates_str: 
            streak += 1
            current -= timedelta(days=1)
        elif (current - timedelta(days=1)).strftime("%Y-%m-%d") in dates_str:
            current -= timedelta(days=1)
        else: return 0
            
        for i in range(len(dates)):
            check_date = current.strftime("%Y-%m-%d")
            if check_date in dates_str:
                if check_date != date.today().strftime("%Y-%m-%d"):
                    streak += 1
                current -= timedelta(days=1)
            else: break
        return streak

    def get_activity_data(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT log_date, COUNT(*) FROM daily_logs GROUP BY log_date")
        data = {str(row[0]): row[1] for row in cursor.fetchall()}
        conn.close()
        return data
        
    def get_total_completions(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM daily_logs")
        try: count = cursor.fetchone()[0]
        except: count = 0
        conn.close()
        return count