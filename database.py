import sqlite3
import os
from datetime import date, timedelta

class Database:
    def __init__(self):
        # This creates a file named 'habits.db' automatically if it doesn't exist
        self.db_name = "habits.db"
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def init_db(self):
        """Creates the tables if they don't exist yet."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Enable Foreign Keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create Habits Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                habit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_name TEXT NOT NULL,
                reminder_time TEXT,
                category TEXT DEFAULT 'General',
                weekly_target INTEGER DEFAULT 0
            )
        """)
        
        # Create Logs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER,
                log_date TEXT,
                FOREIGN KEY(habit_id) REFERENCES habits(habit_id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        conn.close()

    def get_habits(self, category_filter=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # SQLite Query adapted from MySQL
        # We use strftime('%Y-%W', ...) to calculate the current week
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
        # Cascade delete is enabled, but manual delete ensures safety
        cursor.execute("DELETE FROM daily_logs WHERE habit_id = ?", (habit_id,))
        cursor.execute("DELETE FROM habits WHERE habit_id = ?", (habit_id,))
        conn.commit()
        conn.close()

    def toggle_habit(self, habit_id, is_checked):
        conn = self.get_connection()
        cursor = conn.cursor()
        if is_checked:
            # INSERT OR IGNORE avoids duplicates if checked twice quickly
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
        
        # Convert string dates back to Python date objects
        dates = []
        for d_str in dates_str:
            try: dates.append(datetime.strptime(d_str, "%Y-%m-%d").date())
            except: pass # Handle potential parsing errors safely
            
        if not dates: return 0
        
        # (Streak Logic remains mostly the same, just adapted for imports)
        streak = 0
        from datetime import datetime
        current = date.today()
        
        # Check if we did it today
        today_str = current.strftime("%Y-%m-%d")
        if today_str in dates_str: 
            streak += 1
            current -= timedelta(days=1)
        elif (current - timedelta(days=1)).strftime("%Y-%m-%d") in dates_str:
            current -= timedelta(days=1)
        else:
            return 0
            
        # Count backwards
        for i in range(len(dates)):
            check_date = current.strftime("%Y-%m-%d")
            if check_date in dates_str:
                if check_date != date.today().strftime("%Y-%m-%d"): # Don't double count today
                    streak += 1
                current -= timedelta(days=1)
            else:
                break
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
        try:
            count = cursor.fetchone()[0]
        except:
            count = 0
        conn.close()
        return count