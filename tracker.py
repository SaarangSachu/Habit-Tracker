import mysql.connector
from datetime import date
import sys
import os
from dotenv import load_dotenv

# Load the secret variables from .env
load_dotenv()

# --- 1. CONFIGURATION (SECURE) ---
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'), # Reads from .env
    'database': os.getenv('DB_NAME')
}

def get_connection():
    """Establishes connection to the local MySQL database."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"\n❌ CONNECTION ERROR: {err}")
        return None

# --- 2. CORE FUNCTIONS ---

def add_new_habit(name, description):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        query = "INSERT INTO habits (habit_name, description) VALUES (%s, %s)"
        try:
            cursor.execute(query, (name, description))
            conn.commit()
            print(f"\n✅ Success! Added habit: '{name}'")
        except mysql.connector.Error as err:
            print(f"Error adding habit: {err}")
        finally:
            conn.close()

def mark_habit_done(habit_id):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        today = date.today()
        
        check_query = "SELECT * FROM daily_logs WHERE habit_id = %s AND log_date = %s"
        cursor.execute(check_query, (habit_id, today))
        
        if cursor.fetchone():
            print("\n⚠️  You already marked this as done today!")
        else:
            query = "INSERT INTO daily_logs (habit_id, log_date) VALUES (%s, %s)"
            try:
                cursor.execute(query, (habit_id, today))
                conn.commit()
                print("\n🔥 Great job! Habit marked as completed.")
            except mysql.connector.Error as err:
                print(f"Error: {err}")
        conn.close()

def view_daily_progress():
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        print("\n--- 📅 TODAY'S CHECKLIST ---")
        
        today = date.today()
        query = """
        SELECT h.habit_id, h.habit_name, 
               CASE WHEN d.log_id IS NOT NULL THEN '[X]' ELSE '[ ]' END as status
        FROM habits h
        LEFT JOIN daily_logs d ON h.habit_id = d.habit_id AND d.log_date = %s
        """
        cursor.execute(query, (today,))
        
        results = cursor.fetchall()
        if not results:
            print("(No habits found. Add one first!)")
        
        for (hid, name, status) in results:
            print(f"{hid}. {status} {name}")
            
        conn.close()

# --- 3. MAIN MENU ---

def main():
    if get_connection() is None:
        print("Could not connect to database. Check your .env file.")
        sys.exit()

    while True:
        print("\n" + "="*30)
        print("   WINTER ARC TRACKER (CLI)")
        print("="*30)
        print("1. ➕ Add New Habit")
        print("2. 📝 View/Update Daily Checklist")
        print("3. ❌ Exit")
        
        choice = input("\nEnter choice (1-3): ")
        
        if choice == '1':
            name = input("Enter Habit Name: ")
            desc = input("Enter Description: ")
            add_new_habit(name, desc)
        
        elif choice == '2':
            view_daily_progress()
            print("\nType ID to mark done (or Enter to back):")
            user_input = input("> ")
            if user_input.isdigit():
                mark_habit_done(int(user_input))
        
        elif choice == '3':
            print("Keep grinding. Goodbye!")
            break

if __name__ == "__main__":
    main()