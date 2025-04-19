from debug import print
import sys
import subprocess
import hashlib
import json
import datetime
import os
from setup_password import (
    check_password,
    reset_password_with_question,
    ensure_password_exists
)
from PyQt5.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction, QWidget,
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QInputDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, Qt

APP_DIR = "/home/atli/Desktop/Block_python"
HOSTS_FILE = "/etc/hosts"
CLEAN_FILE = f"{APP_DIR}/hosts/hosts.clean"
BLOCKED_FILE = f"{APP_DIR}/hosts/hosts.blocked"
WHITELIST_FILE = f"{APP_DIR}/hosts/hosts.whitelist"
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")

ICON_PATHS = {
    "blocked": f"{APP_DIR}/icons/face-smile.png",
    "unblocked": f"{APP_DIR}/icons/face-angry.png"
}

def get_current_mode():
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f).get("mode", "blacklist")
    except:
        return "blacklist"

def get_block_file():
    mode = get_current_mode()
    return BLOCKED_FILE if mode == "blacklist" else WHITELIST_FILE

def has_sudo_privilege():
    try:
        subprocess.run(["sudo", "cp", BLOCKED_FILE, HOSTS_FILE],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def sha256sum(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        print(f"[ERROR] Failed to hash file {path}: {e}")
        return None

def is_blocked():
    return sha256sum(HOSTS_FILE) == sha256sum(get_block_file())

def block(interactive=True):
    try:
        src_file = get_block_file()
        cmd = ["sudo", "cp", src_file, HOSTS_FILE] if interactive else ["cp", src_file, HOSTS_FILE]
        subprocess.run(cmd, check=True)
        print(f"[DEBUG] ✅ Blocking applied ({get_current_mode()})")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Blocking failed: {e}")

def unblock(interactive=True):
    try:
        cmd = ["sudo", "cp", CLEAN_FILE, HOSTS_FILE] if interactive else ["cp", CLEAN_FILE, HOSTS_FILE]
        subprocess.run(cmd, check=True)
        print("[DEBUG] ✅ Unblock applied")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Unblocking failed: {e}")

def get_current_schedule_state():
    try:
        with open(SETTINGS_FILE, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to load schedule config: {e}")
        return None

    if not config.get("schedule_enabled", False):
        return None

    mode = config.get("mode", "blacklist")
    schedule = config.get("schedule_data", {})

    now = datetime.datetime.now()
    day = now.strftime("%a")
    hour = now.hour
    minute = now.minute

    def get_state(h):
        return schedule.get(f"{day},{h}", 0)

    current = get_state(hour)
    prev = get_state(hour - 1) if hour > 0 else 0

    if mode == "blacklist":
        return "block" if current == 1 or (current == 2 and minute < 30) or (prev == 2 and minute >= 30) else "unblock"
    else:
        return "unblock" if current == 1 or (current == 2 and minute < 30) or (prev == 2 and minute >= 30) else "block"

class FocusTrayApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        QApplication.setQuitOnLastWindowClosed(False)

        self.anchor = QWidget()
        self.anchor.setAttribute(Qt.WA_QuitOnClose, False)
        self.anchor.setWindowFlags(Qt.Tool)
        self.anchor.hide()

        self.tray = QSystemTrayIcon()
        self.menu = QMenu()

        self.toggle_action = QAction("🔁 Toggle Block")
        self.toggle_action.triggered.connect(self.toggle)

        self.settings_action = QAction("⚙️ Settings")
        self.settings_action.triggered.connect(self.open_settings)

        self.change_pass_action = QAction("🔑 Reset Password")
        self.change_pass_action.triggered.connect(lambda: QTimer.singleShot(0, lambda: reset_password_with_question(self.anchor)))

        self.quit_action = QAction("❌ Quit")
        self.quit_action.triggered.connect(self.app.quit)

        self.debug_action = QAction("🧪 Check Schedule")
        self.debug_action.triggered.connect(self.check_schedule)

        self.menu.addAction(self.toggle_action)
        self.menu.addAction(self.settings_action)
        self.menu.addAction(self.change_pass_action)
        self.menu.addSeparator()
        self.menu.addAction(self.debug_action)
        self.menu.addSeparator()
        self.menu.addAction(self.quit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.handle_tray_click)
        self.update_icon()
        self.tray.show()

        # Efficient scheduler
        self.schedule_timer = QTimer()
        self.schedule_timer.timeout.connect(self.check_schedule)
        self.schedule_timer.start(60000)  # every 60s
        self.check_schedule()

    def toggle(self):
        if is_blocked():
            print("[DEBUG] 🔓 Attempting unblock...")
            password, ok = QInputDialog.getText(
                self.anchor, "Unblock", "Enter password:", QLineEdit.Password
            )
            if not ok or not check_password(password):
                print("[DEBUG] ❌ Invalid password")
                return
            unblock()
        else:
            print("[DEBUG] ✅ Toggling block")
            block()
        self.update_icon()

    def open_settings(self):
        if not ensure_password_exists(self.anchor):
            return

        prompt = QDialog(self.anchor)
        prompt.setWindowTitle("Password Required")
        layout = QVBoxLayout(prompt)
        layout.addWidget(QLabel("Enter your password:"))
        input_field = QLineEdit()
        input_field.setEchoMode(QLineEdit.Password)
        layout.addWidget(input_field)
        submit = QPushButton("OK")
        layout.addWidget(submit)
        submit.clicked.connect(prompt.accept)

        if prompt.exec_() == QDialog.Accepted and check_password(input_field.text()):
            subprocess.Popen([sys.executable, os.path.join(APP_DIR, "gui.py")])
        else:
            QMessageBox.warning(self.anchor, "Access Denied", "Incorrect password.")

    def update_icon(self):
        icon = QIcon(ICON_PATHS["blocked" if is_blocked() else "unblocked"])
        self.tray.setIcon(icon)
        mode = get_current_mode().upper()
        self.tray.setToolTip(f"Focus Mode: {mode} — {'ON' if is_blocked() else 'OFF'}")

    def check_schedule(self):
        now = datetime.datetime.now()
        if now.minute not in [0, 30]:
            print(f"[DEBUG] ⏭ Skipping schedule check at {now.strftime('%H:%M')}")
            return

        state = get_current_schedule_state()
        print(f"[DEBUG] 📅 Schedule says: {state}")

        if state == "block" and not is_blocked():
            block()
        elif state == "unblock" and is_blocked():
            unblock()

        self.update_icon()

    def handle_tray_click(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggle()

    def run(self):
        print("[DEBUG] 🧠 Tray app starting...")
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    if "--check" in sys.argv:
        app = QApplication(sys.argv)
        tray = FocusTrayApp()
        tray.check_schedule()
        sys.exit()

    elif "--settings" in sys.argv:
        subprocess.Popen([sys.executable, os.path.join(APP_DIR, "gui.py")])
        sys.exit()

    elif "--reset-password" in sys.argv:
        app = QApplication(sys.argv)
        reset_password_with_question()
        sys.exit()

    app = QApplication(sys.argv)
    tray_app = FocusTrayApp()
    tray_app.run()
