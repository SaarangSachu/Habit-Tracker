import customtkinter as ctk
import mysql.connector
import os
from dotenv import load_dotenv

# --- 1. CONFIGURATION ---
load_dotenv()
ctk.set_appearance_mode("dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

# --- 2. DATABASE CLASS (Same logic as before) ---
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

db = Database()

# --- 3. THE APP CLASS ---
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Winter Arc Tracker")
        self.geometry("400x600")
        self.resizable(False, False)

        # Header
        self.header = ctk.CTkLabel(self, text="MY DAILY ROUTINE", font=("Roboto", 24, "bold"), text_color="#2CC985")
        self.header.pack(pady=20)

        # Scrollable Frame (Holds the list of habits)
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=350, height=400)
        self.scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # Add Habit Section (Bottom)
        self.entry = ctk.CTkEntry(self, placeholder_text="New Habit Name...", width=250)
        self.entry.pack(side="left", padx=(20, 10), pady=20)
        
        self.add_btn = ctk.CTkButton(self, text="Add", width=80, command=self.add_habit_event)
        self.add_btn.pack(side="left", pady=20)

        # Initial Load
        self.load_habits()

    def load_habits(self):
        # 1. Clear existing widgets in the scroll frame
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # 2. Get data from DB
        habits = db.get_habits()

        # 3. Create a Checkbox for each habit
        if not habits:
            label = ctk.CTkLabel(self.scroll_frame, text="No habits yet. Start grinding!", text_color="gray")
            label.pack(pady=20)

        for (h_id, name, is_done) in habits:
            # We use a trick here: passing h_id=h_id into the lambda function
            # so it remembers which ID belongs to which checkbox.
            chk = ctk.CTkCheckBox(
                self.scroll_frame, 
                text=name, 
                font=("Roboto", 16),
                command=lambda id=h_id, n=name: self.on_toggle(id, n)
            )
            
            # Set initial state
            if is_done:
                chk.select()
            
            chk.pack(pady=5, padx=10, anchor="w")
            
            # Save the widget reference so we can find it later if needed
            # (CustomTkinter checkboxes are their own objects)

    def on_toggle(self, habit_id, name):
        # This function runs every time you click a box
        # We need to figure out if it's checked or not.
        # Since we can't easily get the 'value' from the event in this loop,
        # we will simply READ the database state and FLIP it.
        
        # Actually, a simpler way in GUI logic:
        # The checkbox visual state updates automatically.
        # We just need to sync that to the DB.
        
        # Let's verify the state by querying the DB quickly or tracking state in UI.
        # For simplicity, we will assume the user clicked it, so we toggle it.
        
        # But wait! 'command' doesn't pass the new value. 
        # We need to bind the checkbox object to the command.
        pass 

    # --- FIXING THE CHECKBOX LOGIC ---
    # We will rewrite load_habits slightly to handle the click event properly.
    
    def load_habits(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        habits = db.get_habits()

        for (h_id, name, is_done) in habits:
            chk = ctk.CTkCheckBox(
                self.scroll_frame, 
                text=name, 
                font=("Roboto", 16),
            )
            if is_done:
                chk.select()
            
            # We assign the habit_id to the widget itself so we can read it later
            chk.habit_id = h_id
            
            # We set the command to run a specific function passing the widget itself
            chk.configure(command=lambda c=chk: self.checkbox_clicked(c))
            
            chk.pack(pady=10, padx=10, anchor="w")

    def checkbox_clicked(self, checkbox_widget):
        # 1. Get the ID we saved earlier
        h_id = checkbox_widget.habit_id
        # 2. Get the new status (1 = Checked, 0 = Unchecked)
        is_checked = checkbox_widget.get() 
        
        # 3. Update DB
        db.toggle_habit(h_id, is_checked)
        print(f"Habit {h_id} set to {is_checked}")

    def add_habit_event(self):
        text = self.entry.get()
        if text:
            db.add_habit(text)
            self.entry.delete(0, "end")
            self.load_habits()

if __name__ == "__main__":
    app = App()
    app.mainloop()