import mysql.connector
import os
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv()

class Database:
    def get_connection(self):
        return mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            database=os.getenv('DB_NAME')
        )

    # UPDATED: Now fetches category
    def get_habits(self, category_filter=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT h.habit_id, h.habit_name, h.reminder_time, h.category,
               CASE WHEN d.log_id IS NOT NULL THEN 1 ELSE 0 END as is_done
        FROM habits h
        LEFT JOIN daily_logs d ON h.habit_id = d.habit_id AND d.log_date = CURDATE()
        """
        
        # Add Filter Logic
        if category_filter and category_filter != "All":
            query += f" WHERE h.category = '{category_filter}'"
            
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        return result

    # UPDATED: Accepts category
    def add_habit(self, name, time_str, category):
        conn = self.get_connection()
        cursor = conn.cursor()
        if time_str == "": time_str = None
        cursor.execute("INSERT INTO habits (habit_name, reminder_time, category) VALUES (%s, %s, %s)", (name, time_str, category))
        conn.commit()
        conn.close()

    # NEW: Update Function for Editing
    def update_habit(self, habit_id, name, time_str, category):
        conn = self.get_connection()
        cursor = conn.cursor()
        if time_str == "": time_str = None
        cursor.execute("UPDATE habits SET habit_name=%s, reminder_time=%s, category=%s WHERE habit_id=%s", 
                       (name, time_str, category, habit_id))
        conn.commit()
        conn.close()

    def delete_habit(self, habit_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM daily_logs WHERE habit_id = %s", (habit_id,))
        cursor.execute("DELETE FROM habits WHERE habit_id = %s", (habit_id,))
        conn.commit()
        conn.close()

    def toggle_habit(self, habit_id, is_checked):
        conn = self.get_connection()
        cursor = conn.cursor()
        if is_checked:
            cursor.execute("INSERT IGNORE INTO daily_logs (habit_id, log_date) VALUES (%s, CURDATE())", (habit_id,))
        else:
            cursor.execute("DELETE FROM daily_logs WHERE habit_id = %s AND log_date = CURDATE()", (habit_id,))
        conn.commit()
        conn.close()

    def get_streak(self, habit_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT log_date FROM daily_logs WHERE habit_id = %s ORDER BY log_date DESC", (habit_id,))
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()
        if not dates: return 0
        streak = 0
        current = date.today()
        if current in dates: streak += 1; current -= timedelta(days=1)
        elif (current - timedelta(days=1)) in dates: current -= timedelta(days=1)
        else: return 0
        for d in dates:
            if d == current:
                if d != date.today(): streak += 1
                current -= timedelta(days=1)
        return streak

    def get_activity_data(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT log_date, COUNT(*) FROM daily_logs GROUP BY log_date")
        data = {str(row[0]): row[1] for row in cursor.fetchall()}
        conn.close()
        return data