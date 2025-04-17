import sys
import subprocess
import hashlib
import json
import datetime
import os
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer

# Paths
APP_DIR = "/home/atli/Desktop/Block_python"
HOSTS_FILE = "/etc/hosts"
CLEAN_FILE = f"{APP_DIR}/hosts/hosts.clean"
BLOCKED_FILE = f"{APP_DIR}/hosts/hosts.blocked"
ICON_BLOCKED = f"{APP_DIR}/icons/face-smile.png"
ICON_UNBLOCKED = f"{APP_DIR}/icons/face-angry.png"

def md5sum(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def is_blocked():
    return md5sum(HOSTS_FILE) == md5sum(BLOCKED_FILE)

def block(interactive=True):
    try:
        cmd = ["pkexec", "cp", BLOCKED_FILE, HOSTS_FILE] if interactive else ["cp", BLOCKED_FILE, HOSTS_FILE]
        result = subprocess.run(cmd)
        print("Block result:", result.returncode)
    except Exception as e:
        print("Failed to enable blocking:", e)

def unblock(interactive=True):
    try:
        cmd = ["pkexec", "cp", CLEAN_FILE, HOSTS_FILE] if interactive else ["cp", CLEAN_FILE, HOSTS_FILE]
        result = subprocess.run(cmd)
        print("Unblock result:", result.returncode)
    except Exception as e:
        print("Failed to disable blocking:", e)

APP_DIR = "/home/atli/Desktop/Block_python"
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")

def get_current_schedule_state():
    try:
        with open(SETTINGS_FILE, "r") as f:
            config = json.load(f)
    except Exception:
        return None

    if not config.get("schedule_enabled", False):
        return None

    mode = config.get("mode", "blacklist")
    schedule = config.get("schedule_data", {})

    now = datetime.datetime.now()
    now = datetime.datetime(now.year, now.month, now.day, 13, 15)
    day = now.strftime("%a")  # E.g. 'Mon'
    hour = now.hour
    minute = now.minute

    def get_state(h):
        return schedule.get(f"{day},{h}", 0)

    current = get_state(hour)
    prev = get_state(hour - 1) if hour > 0 else 0

    if mode == "blacklist":
        # Block ONLY during scheduled times
        if current == 1:
            return "block"
        if current == 2 and minute < 30:
            return "block"
        if prev == 2 and minute >= 30:
            return "block"
        return "unblock"
    
    elif mode == "whitelist":
        # Unblock ONLY during scheduled times
        if current == 1:
            return "unblock"
        if current == 2 and minute < 30:
            return "unblock"
        if prev == 2 and minute >= 30:
            return "unblock"
        return "block"

    return "unblock"


class FocusTrayApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.tray = QSystemTrayIcon()
        self.menu = QMenu()

        # Create tray actions
        self.toggle_action = QAction("🔁 on/off")
        self.toggle_action.triggered.connect(self.toggle)

        self.quit_action = QAction("❌ Quit")
        self.quit_action.triggered.connect(self.app.quit)

        self.settings_action = QAction("⚙️ Settings")
        self.settings_action.triggered.connect(self.open_settings)
        
        self.menu.addAction(self.toggle_action)
        self.menu.addAction(self.settings_action)
        self.menu.addSeparator()
        self.menu.addAction(self.quit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.setToolTip("Focus Mode Toggle")
        self.update_icon()
        self.tray.show()

        self.tray.activated.connect(self.handle_tray_click)

        # Auto-refresh icon every 5 seconds in case of external change
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_icon)
        self.timer.start(5000)
        self.schedule_timer = QTimer()
        self.schedule_timer.timeout.connect(self.check_schedule)
        self.schedule_timer.start(60000)  # Every 60 seconds
        self.check_schedule()  # Run once on startup

        #debug
        self.debug_action = QAction("🧪 Check Schedule Now")
        self.debug_action.triggered.connect(self.check_schedule)
        self.menu.addAction(self.debug_action)


    def toggle(self):
        if is_blocked():
            unblock()
        else:
            block()
        self.update_icon()

    def update_icon(self):
        if is_blocked():
            self.tray.setIcon(QIcon(ICON_BLOCKED))
            self.tray.setToolTip("Focus Mode ON: Distractions Blocked")
        else:
            self.tray.setIcon(QIcon(ICON_UNBLOCKED))
            self.tray.setToolTip("Focus Mode OFF: Distractions Allowed")

    def open_settings(self):
        subprocess.Popen(["python3", os.path.join(APP_DIR, "gui.py")])

    def run(self):
        sys.exit(self.app.exec_())

    def handle_tray_click(self, reason):
        if reason == QSystemTrayIcon.Trigger:
           self.toggle()
    
    def check_schedule(self):
        action = get_current_schedule_state()
        print(f"[DEBUG] Schedule check: {action} at simulated 13:15")
    
        if action == "block" and not is_blocked():
            print("→ Triggering block")
            block()
            self.update_icon()
        elif action == "unblock" and is_blocked():
            print("→ Triggering unblock")
            unblock()
            self.update_icon()


if __name__ == "__main__":
    if "--check" in sys.argv:
        action = get_current_schedule_state()
        print(f"[Manual Trigger] Schedule check: {action}")
        if action == "block" and not is_blocked():
            block()
        elif action == "unblock" and is_blocked():
            unblock()
        sys.exit()
    else:
        app = FocusTrayApp()
        app.run()
