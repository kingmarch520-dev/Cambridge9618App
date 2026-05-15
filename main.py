import sys
import os
import sqlite3
import requests
from datetime import datetime

# 1. PATH FORCING FOR COMPILATION
pydroid_packages = "/data/user/0/ru.iiec.pydroid3/files/aarch64-linux-android/lib/python3.13/site-packages"
if pydroid_packages not in sys.path:
    sys.path.insert(0, pydroid_packages)

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.slider import MDSlider
from kivymd.uix.button import MDRaisedButton
from kivy.uix.popup import Popup

DB_NAME = 'cambridge_9618.db'

# =====================================================================
# AUTO-GENERATION DATABASE & BACKEND LOGIC
# =====================================================================
def initialize_production_database():
    """Ensures the database and official 9618 syllabus exist on app launch."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            last_online_date TEXT,
            is_admin INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS syllabus_topics (
            topic_id INTEGER PRIMARY KEY,
            syllabus_section TEXT NOT NULL,
            topic_name TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            topic_id INTEGER,
            score_percentage REAL NOT NULL,
            date_logged TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (topic_id) REFERENCES syllabus_topics (topic_id)
        )
    ''')

    official_9618_data = [
        (1, "Section 1: AS Level Theory", "1 Information representation"),
        (2, "Section 1: AS Level Theory", "2 Communication"),
        (3, "Section 1: AS Level Theory", "3 Hardware"),
        (4, "Section 1: AS Level Theory", "4 Processor Fundamentals"),
        (5, "Section 1: AS Level Theory", "5 System Software"),
        (6, "Section 1: AS Level Theory", "6 Security, privacy and data integrity"),
        (7, "Section 1: AS Level Theory", "7 Ethics and Ownership"),
        (8, "Section 1: AS Level Theory", "8 Databases"),
        (9, "Section 2: AS Level Skills", "9 Algorithm Design and Problem-solving"),
        (10, "Section 2: AS Level Skills", "10 Data Types and Structures"),
        (11, "Section 2: AS Level Skills", "11 Programming"),
        (12, "Section 2: AS Level Skills", "12 Software Development"),
        (13, "Section 3: A Level Theory", "13 Data Representation"),
        (14, "Section 3: A Level Theory", "14 Communication and internet technologies"),
        (15, "Section 3: A Level Theory", "15 Hardware and Virtual Machines"),
        (16, "Section 3: A Level Theory", "16 System Software"),
        (17, "Section 3: A Level Theory", "17 Security"),
        (18, "Section 3: A Level Theory", "18 Artificial Intelligence (AI)"),
        (19, "Section 4: A Level Skills", "19 Computational thinking and Problem-solving"),
        (20, "Section 4: A Level Skills", "20 Further Programming")
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO syllabus_topics VALUES (?, ?, ?)', official_9618_data)
    
    # Pre-seed Anopa's baseline profile if table is brand new
    cursor.execute("SELECT count(*) FROM users WHERE username='Anopa'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (id, username, password, last_online_date) VALUES (1, 'Anopa', '9618', '2026-05-14')")
        cursor.execute("INSERT INTO performance_logs (user_id, topic_id, score_percentage, date_logged) VALUES (1, 4, 37.0, '2026-05-14')")

    conn.commit()
    conn.close()

def backend_check_internet():
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except (requests.ConnectionError, requests.Timeout):
        return False

def backend_fetch_weak_spot(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.topic_name, AVG(p.score_percentage) as average_mark
        FROM performance_logs p
        JOIN syllabus_topics t ON p.topic_id = t.topic_id
        WHERE p.user_id = ?
        GROUP BY p.topic_id
        ORDER BY average_mark ASC LIMIT 1
    ''', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row

# =====================================================================
# GRAPHICAL APP FRAMEWORK
# =====================================================================
class CambridgeStudyApp(MDApp):
    def build(self):
        initialize_production_database()
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepPurple"
        
        self.current_user_id = 1
        self.current_username = "Anopa"
        
        sm = MDScreenManager()
        main_screen = MDScreen(name="main")
        nav = MDBottomNavigation()
        
        # TAB 1: DASHBOARD
        dashboard_tab = MDBottomNavigationItem(name="dashboard", text="Dashboard", icon="view-dashboard")
        dash_layout = MDBoxLayout(orientation='vertical', padding=20, spacing=20)
        
        title_card = MDCard(size_hint=(1, 0.2), padding=15, elevation=2)
        title_card.add_widget(MDLabel(text=f"Student Profile: {self.current_username}\nTarget: CAIE 9618 (2027-2029)", font_style="H6"))
        dash_layout.add_widget(title_card)
        
        weak_data = backend_fetch_weak_spot(self.current_user_id)
        weakspot_card = MDCard(size_hint=(1, 0.25), padding=15, elevation=4)
        if weak_data:
            topic_name, avg_score = weak_data
            weakspot_card.md_bg_color = [0.8, 0.2, 0.2, 0.15]
            weak_text = f"⚠️ LIVE WEAKNESS REPORT:\n\n{topic_name}\nRunning Board Score: {avg_score:.1f}%"
            lbl_color = "Error"
        else:
            weakspot_card.md_bg_color = [0.2, 0.8, 0.2, 0.15]
            weak_text = "✨ NO LIVE WEAK SPOTS FOUND!"
            lbl_color = "Primary"
            
        weakspot_card.add_widget(MDLabel(text=weak_text, font_style="Subtitle1", theme_text_color=lbl_color))
        dash_layout.add_widget(weakspot_card)
        
        focus_card = MDCard(size_hint=(1, 0.3), padding=15, elevation=4, orientation='vertical', spacing=10)
        focus_card.md_bg_color = [0.2, 0.6, 0.8, 0.15]
        focus_card.add_widget(MDLabel(text="📱 DISTRACTION CONTROL ENVIRONMENT", font_style="H6"))
        focus_card.add_widget(MDLabel(text=f"Internet connection status: {'ONLINE' if backend_check_internet() else 'OFFLINE'}", font_style="Caption"))
        
        focus_btn = MDRaisedButton(text="ACTIVATE ACCELERATED FOCUS", size_hint=(1, None))
        focus_btn.bind(on_release=self.trigger_focus_lockout)
        focus_card.add_widget(focus_btn)
        dash_layout.add_widget(focus_card)
        
        dash_layout.add_widget(MDBoxLayout())
        dashboard_tab.add_widget(dash_layout)
        
        # TAB 2: PAPERS
        papers_tab = MDBottomNavigationItem(name="papers", text="Papers", icon="file-document-multiple")
        papers_layout = MDBoxLayout(orientation='vertical', padding=20)
        papers_layout.add_widget(MDLabel(text="Cambridge 9618 Cloud Sync System\n(Awaiting GitHub Remote Push)", halign="center", font_style="H6"))
        papers_tab.add_widget(papers_layout)
        
        # TAB 3: SETTINGS
        settings_tab = MDBottomNavigationItem(name="settings", text="Settings", icon="cog")
        settings_layout = MDBoxLayout(orientation='vertical', padding=20, spacing=30)
        settings_layout.add_widget(MDLabel(text="Dynamic Personalization Settings", font_style="H5", halign="center"))
        
        self.rainbow_slider = MDSlider(min=0, max=10, value=3, step=1, size_hint=(1, 0.2))
        self.rainbow_slider.bind(value=self.shift_ui_palette)
        settings_layout.add_widget(self.rainbow_slider)
        settings_layout.add_widget(MDBoxLayout())
        settings_tab.add_widget(settings_layout)
        
        nav.add_widget(dashboard_tab)
        nav.add_widget(papers_tab)
        nav.add_widget(settings_tab)
        main_screen.add_widget(nav)
        sm.add_widget(main_screen)
        return sm

    def trigger_focus_lockout(self, instance):
        content = MDBoxLayout(orientation='vertical', padding=20, spacing=20)
        content.add_widget(MDLabel(
            text="🔒 OVERLAY BANNER ACTIVE\n\nStudy Mode is locked. Close down your TikTok app and complete your revision sheets first!",
            halign="center", font_style="Subtitle1", theme_text_color="Custom", text_color=[1,1,1,1]
        ))
        close_btn = MDRaisedButton(text="Session Complete", size_hint=(1, None))
        content.add_widget(close_btn)
        popup = Popup(title="Distraction Blocked", content=content, size_hint=(0.9, 0.5), auto_dismiss=False)
        close_btn.bind(on_release=popup.dismiss)
        popup.open()

    def shift_ui_palette(self, instance, value):
        palettes = ["Red", "Pink", "Purple", "DeepPurple", "Indigo", "Blue", "Teal", "Green", "Orange", "DeepOrange", "Brown"]
        index = int(max(0, min(value, len(palettes) - 1)))
        try:
            self.theme_cls.primary_palette = palettes[index]
        except Exception:
            pass

if __name__ == "__main__":
    CambridgeStudyApp().run()
