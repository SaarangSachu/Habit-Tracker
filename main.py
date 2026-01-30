import customtkinter as ctk
import threading
import time
import os
from plyer import notification
from datetime import datetime

# Import Custom Modules
from database import Database
from components import HabitCard, Sidebar, resource_path
from clock_widget import RealTimeClock 
from sounds import SoundManager
from analytics import AnalyticsPanel, PerformancePanel

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("QuestLog v1.3")
        self.geometry("1100x700")
        
        # --- LOAD WINDOW ICON ---
        try:
            icon_path = resource_path(os.path.join("assets", "logo.ico"))
            self.iconbitmap(icon_path)
        except Exception:
            pass # Fails gracefully if no icon found

        self.db = Database()
        self.sound = SoundManager()
        
        self.total_xp = 0
        self.level = 1
        self.next_level_xp = 100
        self.editing_id = None
        self.current_filter = "All"
        
        self.stop_thread = False
        self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.thread.start()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.calculate_xp()
        self.sidebar = None
        self.refresh_sidebar()

        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        
        self.show_dashboard()

    def calculate_xp(self):
        completions = self.db.get_total_completions()
        self.total_xp = completions * 10
        if self.total_xp < 100: self.level = 1; self.next_level_xp = 100
        elif self.total_xp < 300: self.level = 2; self.next_level_xp = 300
        elif self.total_xp < 600: self.level = 3; self.next_level_xp = 600
        elif self.total_xp < 1000: self.level = 4; self.next_level_xp = 1000
        else: self.level = 5; self.next_level_xp = 5000

    def refresh_sidebar(self):
        if self.sidebar: self.sidebar.destroy()
        self.sidebar = Sidebar(self, self.navigate, self.total_xp, self.level, self.next_level_xp, self.change_theme)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

    def change_theme(self, theme_name):
        if theme_name == "cyberpunk":
            ctk.set_default_color_theme("dark-blue") 
            notification.notify(title="Theme Unlocked!", message="Cyberpunk mode active.", timeout=3)

    def run_scheduler(self):
        while not self.stop_thread:
            current_time = datetime.now().strftime("%H:%M")
            try:
                habits = self.db.get_habits(category_filter="All")
                for (h_id, name, remind_time, cat, target, is_done, progress) in habits:
                    if remind_time and not is_done:
                        if remind_time == current_time:
                            self.sound.play_notification()
                            notification.notify(title="Quest Alert!", message=f"Time to complete: {name}", timeout=10)
                            time.sleep(60)
            except: pass
            time.sleep(10)

    def navigate(self, page_name):
        if page_name == "dashboard": self.show_dashboard()
        elif page_name == "analytics": self.show_analytics()
        elif page_name == "performance": self.show_performance()
        elif page_name == "settings": self.open_settings_modal()

    def show_dashboard(self):
        self.clear_frame()
        # Header
        header = ctk.CTkFrame(self.main_area, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="Current Quests", font=("Segoe UI", 32, "bold")).pack(side="left")
        RealTimeClock(header).pack(side="left", padx=20)

        # Controls
        ctrl = ctk.CTkFrame(self.main_area, fg_color="#2b2b2b", corner_radius=10)
        ctrl.pack(fill="x", pady=(0, 20), ipady=5)
        self.name_entry = ctk.CTkEntry(ctrl, placeholder_text="New Quest Name...", width=200)
        self.name_entry.pack(side="left", padx=(15, 5), pady=10)
        
        self.cats_data = self.db.get_all_categories() 
        self.cat_names = [c[1] for c in self.cats_data]
        self.cat_var = ctk.StringVar(value=self.cat_names[0] if self.cat_names else "General")
        self.cat_menu = ctk.CTkComboBox(ctrl, values=self.cat_names, variable=self.cat_var, width=110, state="readonly")
        self.cat_menu.pack(side="left", padx=5)

        ctk.CTkButton(ctrl, text="+", width=30, fg_color="#444", command=self.open_new_category_modal).pack(side="left", padx=2)
        ctk.CTkButton(ctrl, text="⚙️", width=30, fg_color="#333", command=self.open_manage_categories_modal).pack(side="left", padx=2)

        self.freq_var = ctk.StringVar(value="Daily")
        freq_opts = ["Daily", "1x / Week", "2x / Week", "3x / Week", "4x / Week", "5x / Week", "6x / Week", "7x / Week"]
        ctk.CTkComboBox(ctrl, values=freq_opts, variable=self.freq_var, width=110, state="readonly").pack(side="left", padx=5)

        ctk.CTkLabel(ctrl, text="At:", text_color="grey").pack(side="left", padx=(10, 2))
        self.time_entry = ctk.CTkEntry(ctrl, placeholder_text="09:00", width=70)
        self.time_entry.pack(side="left", padx=2)

        self.action_btn = ctk.CTkButton(ctrl, text="+ Add", width=80, command=self.save_habit_event)
        self.action_btn.pack(side="left", padx=15)
        self.cancel_btn = ctk.CTkButton(ctrl, text="✕", width=30, fg_color="#444", command=self.cancel_edit)

        # Filters
        filters = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent", height=50, orientation="horizontal")
        filters.pack(fill="x", pady=(0, 10))
        for cat in ["All"] + self.cat_names:
            col = "#2CC985" if self.current_filter == cat else "transparent"
            txt = "white" if self.current_filter == cat else "grey"
            ctk.CTkButton(filters, text=cat, width=60, height=25, fg_color=col, text_color=txt, corner_radius=20, 
                          command=lambda c=cat: self.set_filter(c)).pack(side="left", padx=5)

        # List
        self.progress = ctk.CTkProgressBar(self.main_area, height=10, corner_radius=8)
        self.progress.pack(fill="x", pady=(0, 15))
        self.progress.set(0)
        self.scroll_frame = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)
        self.load_habits_list()

    # --- MODALS ---
    def open_new_category_modal(self): self.open_category_form(is_edit=False)
    def open_manage_categories_modal(self):
        top = ctk.CTkToplevel(self)
        top.title("Manage Categories")
        top.geometry("350x400")
        top.attributes("-topmost", True)
        ctk.CTkLabel(top, text="Edit Categories", font=("Segoe UI", 18, "bold")).pack(pady=15)
        scroll = ctk.CTkScrollableFrame(top, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        for (cat_id, name, color) in self.cats_data:
            row = ctk.CTkFrame(scroll, fg_color="#2b2b2b")
            row.pack(fill="x", pady=5)
            ctk.CTkFrame(row, width=15, height=15, fg_color=color).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=name, font=("Arial", 12)).pack(side="left")
            ctk.CTkButton(row, text="Edit", width=50, height=25, fg_color="#444", 
                          command=lambda cid=cat_id, n=name, c=color: self.open_edit_category_modal(cid, n, c, top)).pack(side="right", padx=10)

    def open_edit_category_modal(self, cat_id, current_name, current_color, parent):
        parent.destroy()
        self.open_category_form(is_edit=True, cat_id=cat_id, default_name=current_name, default_color=current_color)

    def open_category_form(self, is_edit=False, cat_id=None, default_name="", default_color=None):
        top = ctk.CTkToplevel(self)
        top.title("Category Form")
        top.geometry("300x280")
        top.attributes("-topmost", True)
        entry = ctk.CTkEntry(top, placeholder_text="Category Name")
        entry.pack(pady=15, padx=20, fill="x")
        if default_name: entry.insert(0, default_name)
        colors = {"Neon Red": "#FF0055", "Neon Blue": "#00CCFF", "Neon Purple": "#BD00FF", "Neon Yellow": "#F9F871", "Cyan": "#00E5FF", "Hot Pink": "#FF4081", "Orange": "#FF9100", "Lime": "#76FF03"}
        inv_map = {v: k for k, v in colors.items()}
        color_var = ctk.StringVar(value=inv_map.get(default_color, "Neon Blue"))
        ctk.CTkComboBox(top, values=list(colors.keys()), variable=color_var).pack(pady=5, padx=20, fill="x")
        def save():
            name = entry.get()
            col = colors.get(color_var.get(), "#FFF")
            if name:
                if is_edit: self.db.update_category(cat_id, name, col)
                else: self.db.add_category(name, col)
                self.show_dashboard()
                top.destroy()
        ctk.CTkButton(top, text="Save", command=save, fg_color="#2CC985").pack(pady=20)

    def open_settings_modal(self):
        top = ctk.CTkToplevel(self)
        top.title("Settings")
        top.geometry("300x250")
        top.attributes("-topmost", True)
        ctk.CTkLabel(top, text="System Configuration", font=("Segoe UI", 16, "bold")).pack(pady=15)
        
        sound_frame = ctk.CTkFrame(top, fg_color="transparent")
        sound_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(sound_frame, text="Audio").pack(side="left")
        def toggle_sound():
            is_muted = self.sound.toggle_mute()
            sound_btn.configure(text="🔇 Muted" if is_muted else "🔊 On", fg_color="#444" if is_muted else "#2CC985")
        current_text = "🔇 Muted" if self.sound.is_muted else "🔊 On"
        current_col = "#444" if self.sound.is_muted else "#2CC985"
        sound_btn = ctk.CTkButton(sound_frame, text=current_text, width=80, fg_color=current_col, command=toggle_sound)
        sound_btn.pack(side="right")

        ctk.CTkLabel(top, text="Danger Zone", text_color="#e74c3c", font=("Arial", 12, "bold")).pack(pady=(20, 5))
        def reset_data():
            conn = self.db.get_connection()
            conn.execute("DELETE FROM daily_logs"); conn.execute("DELETE FROM habits"); conn.commit(); conn.close()
            self.total_xp = 0; self.calculate_xp(); self.refresh_sidebar(); self.show_dashboard()
            top.destroy()
            notification.notify(title="System Reset", message="Data wiped.", timeout=3)
        ctk.CTkButton(top, text="☢️ RESET ALL DATA", fg_color="#c0392b", hover_color="#e74c3c", command=reset_data).pack(pady=10)

    # --- CORE FUNCTIONS ---
    def set_filter(self, category):
        self.current_filter = category
        self.show_dashboard()

    def load_habits_list(self):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        habits = self.db.get_habits(self.current_filter)
        cats_data = self.db.get_all_categories()
        color_map = {cat[1]: cat[2] for cat in cats_data}
        done = 0
        for (h_id, name, remind_time, category, target, is_done, progress) in habits:
            streak = self.db.get_streak(h_id)
            if is_done: done += 1
            disp_time = remind_time if remind_time else ""
            card_col = color_map.get(category, "#888")
            HabitCard(self.scroll_frame, h_id, name, disp_time, category, card_col, target, progress, is_done, streak, 
                      self.toggle_habit, self.delete_habit_event, self.start_edit_event).pack(fill="x", pady=6)
        if len(habits) > 0: self.progress.set(done / len(habits))
        else: self.progress.set(0)

    def save_habit_event(self):
        name = self.name_entry.get()
        time_val = self.time_entry.get().strip()
        cat = self.cat_var.get()
        freq = self.freq_var.get()
        target = 0 if freq == "Daily" else int(freq[0])
        try: valid_time = datetime.strptime(time_val, "%H:%M").strftime("%H:%M") if time_val else ""
        except: valid_time = ""
        if name:
            if self.editing_id: self.db.update_habit(self.editing_id, name, valid_time, cat, target); self.cancel_edit()
            else: self.db.add_habit(name, valid_time, cat, target); self.name_entry.delete(0, "end"); self.time_entry.delete(0, "end")
            self.load_habits_list()

    def start_edit_event(self, h_id, name, time_val, category, target):
        self.editing_id = h_id
        self.name_entry.delete(0, "end"); self.name_entry.insert(0, name)
        self.time_entry.delete(0, "end"); 
        if time_val: self.time_entry.insert(0, time_val)
        self.cat_var.set(category if category in self.cat_names else "General")
        self.freq_var.set("Daily" if target == 0 else f"{target}x / Week")
        self.action_btn.configure(text="💾 Save", fg_color="#e67e22")
        self.cancel_btn.pack(side="left", padx=5)

    def cancel_edit(self):
        self.editing_id = None
        self.name_entry.delete(0, "end"); self.time_entry.delete(0, "end")
        self.freq_var.set("Daily"); self.action_btn.configure(text="+ Add", fg_color="#2CC985"); self.cancel_btn.pack_forget()

    def toggle_habit(self, h_id, is_checked):
        self.db.toggle_habit(h_id, is_checked)
        if is_checked: self.sound.play_success()
        self.calculate_xp(); self.refresh_sidebar(); self.load_habits_list()

    def delete_habit_event(self, h_id):
        self.db.delete_habit(h_id)
        if self.editing_id == h_id: self.cancel_edit()
        self.calculate_xp(); self.refresh_sidebar(); self.load_habits_list()

    def show_analytics(self): 
        self.clear_frame(); AnalyticsPanel(self.main_area, self.db).pack(fill="both", expand=True)
    def show_performance(self):
        self.clear_frame(); PerformancePanel(self.main_area, self.db).pack(fill="both", expand=True)
    def clear_frame(self):
        for w in self.main_area.winfo_children(): w.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()