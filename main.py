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
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")

ICON_PATHS = {
    "blocked": f"{APP_DIR}/icons/face-smile.png",
    "unblocked": f"{APP_DIR}/icons/face-angry.png"
}

def is_first_run():
    return not (
        os.path.exists(os.path.join(APP_DIR, "password.hash")) and
        os.path.exists(os.path.join(APP_DIR, "secret_qa.json")) and
        os.path.exists(os.path.join(APP_DIR, "settings.json"))
    )
def first_run_setup(parent=None):
    print("[SETUP] 🚀 First time setup starting")

    # Step 1: Set secret question
    question, ok = QInputDialog.getText(parent, "Security Setup", "Set a secret question:")
    if not ok or not question.strip():
        QMessageBox.warning(parent, "Cancelled", "Setup cancelled.")
        sys.exit()

    answer, ok = QInputDialog.getText(parent, "Security Setup", "Answer to your secret question:", QLineEdit.Password)
    if not ok or not answer.strip():
        QMessageBox.warning(parent, "Cancelled", "Setup cancelled.")
        sys.exit()

    # Save secret QA
    import bcrypt

    hashed_answer = bcrypt.hashpw(answer.encode(), bcrypt.gensalt())
    with open(os.path.join(APP_DIR, "secret_qa.json"), "w") as f:
            json.dump({
                "question": question.strip(),
                "answer": hashed_answer.decode()
            }, f)

    print("[SETUP] ✅ Secret QA saved")

    # Step 2: Set app password
    password, ok = QInputDialog.getText(parent, "Create Password", "Set your app password:", QLineEdit.Password)
    if not ok or not password.strip():
        QMessageBox.warning(parent, "Cancelled", "Setup cancelled.")
        sys.exit()

    # Save password
    import bcrypt
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    with open(os.path.join(APP_DIR, "password.hash"), "wb") as f:
        f.write(hashed)

    print("[SETUP] ✅ Password hash saved")

    # Step 3: Request system permission
    if not has_sudo_privilege():
        answer = QMessageBox.question(
            parent,
            "Permission Required",
            "FocusBlocker needs permission to manage your hosts file.\nWould you like to allow it now?",
            QMessageBox.Yes | QMessageBox.No
        )
        if answer == QMessageBox.Yes:
            try:
                subprocess.run(["pkexec", os.path.join(APP_DIR, "install_sudoers.sh")], check=True)
                print("[SETUP] ✅ Sudo rule installed")
            except Exception as e:
                print(f"[SETUP ERROR] 🔐 Failed to configure sudo: {e}")
                QMessageBox.critical(parent, "Error", "System permission could not be configured.\nBlocking will require a password every time.")

    # Step 4: Init settings
    with open(SETTINGS_FILE, "w") as f:
        json.dump({
            "mode": "blacklist",
            "schedule_enabled": False,
            "schedule_data": {}
        }, f, indent=4)

    print("[SETUP] 🎉 First-time setup complete!")
    QMessageBox.information(parent, "Setup Complete", "You're ready to block distractions!")

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
    return sha256sum(HOSTS_FILE) == sha256sum(BLOCKED_FILE)


def block(interactive=True):
    try:
        cmd = ["sudo", "cp", BLOCKED_FILE, HOSTS_FILE] if interactive else ["cp", BLOCKED_FILE, HOSTS_FILE]
        subprocess.run(cmd, check=True)
        print("[DEBUG] ✅ Hosts file replaced with BLOCKED version")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Blocking failed: {e}")


def unblock(interactive=True):
    try:
        cmd = ["sudo", "cp", CLEAN_FILE, HOSTS_FILE] if interactive else ["cp", CLEAN_FILE, HOSTS_FILE]
        subprocess.run(cmd, check=True)
        print("[DEBUG] ✅ Hosts file replaced with CLEAN version")
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
        if current == 1 or (current == 2 and minute < 30) or (prev == 2 and minute >= 30):
            return "block"
        return "unblock"
    elif mode == "whitelist":
        if current == 1 or (current == 2 and minute < 30) or (prev == 2 and minute >= 30):
            return "unblock"
        return "block"


class FocusTrayApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        QApplication.setQuitOnLastWindowClosed(False)

        self.anchor = QWidget()
        self.anchor.setAttribute(Qt.WA_QuitOnClose, False)
        self.anchor.setWindowFlags(Qt.Tool)
        self.anchor.hide()

        # 🔐 One-time sudo permission installer
        if not has_sudo_privilege():
            answer = QMessageBox.question(
                self.anchor,
                "Permission Needed",
                "FocusBlocker needs permission to block websites without asking every time.\n\nWould you like to allow this now?",
                QMessageBox.Yes | QMessageBox.No
            )
            if answer == QMessageBox.Yes:
                try:
                    subprocess.run(["pkexec", os.path.join(APP_DIR, "install_sudoers.sh")], check=True)
                    print("[DEBUG] ✅ Sudo rule installed")
                except Exception as e:
                    print(f"[ERROR] Failed to install sudo rule: {e}")
                    QMessageBox.critical(self.anchor, "Error", "Could not configure system permission.\nBlocking will require password every time.")

        self.tray = QSystemTrayIcon()
        self.menu = QMenu()

        self.toggle_action = QAction("🔁 Toggle Block")
        self.toggle_action.triggered.connect(lambda: print("🔁 Toggle triggered") or self.toggle())

        self.settings_action = QAction("⚙️ Settings")
        self.settings_action.triggered.connect(lambda: print("⚙️ Settings triggered") or self.open_settings())

        self.change_pass_action = QAction("🔑 Reset Password")
        self.change_pass_action.triggered.connect(lambda: print("🔑 Reset Password triggered") or QTimer.singleShot(0, lambda: reset_password_with_question(self.anchor)))

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
        self.tray.setToolTip("Focus Mode Toggle")
        self.update_icon()
        self.tray.show()

        self.tray.activated.connect(self.handle_tray_click)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_icon)
        self.timer.start(5000)

        self.schedule_timer = QTimer()
        self.schedule_timer.timeout.connect(self.check_schedule)
        self.schedule_timer.start(60000)
        self.check_schedule()

    def toggle(self):
        try:
            if is_blocked():
                print("[DEBUG] 🔐 Attempting unblock — prompt for password")
                password, ok = QInputDialog.getText(
                    self.anchor, "Enter Password", "Enter your password:", QLineEdit.Password
                )
                if not ok or not password.strip():
                    print("[DEBUG] 🚫 Unblock cancelled by user")
                    return
                if not check_password(password):
                    print("[DEBUG] ❌ Incorrect password")
                    QMessageBox.warning(self.anchor, "Access Denied", "Incorrect password.")
                    return
                print("[DEBUG] ✅ Password correct — unblocking now")
                unblock()
            else:
                print("[DEBUG] ✅ Blocking without password")
                block()
            self.update_icon()
        except Exception as e:
            print(f"[ERROR] Toggle failed: {e}")
            QMessageBox.critical(self.anchor, "Error", f"Toggle failed: {e}")

    def update_icon(self):
        icon_path = ICON_PATHS["blocked"] if is_blocked() else ICON_PATHS["unblocked"]
        self.tray.setIcon(QIcon(icon_path))
        self.tray.setToolTip("Focus Mode ON" if is_blocked() else "Focus Mode OFF")

    def open_settings(self):
        if not ensure_password_exists(self.anchor):
            print("[DEBUG] ❌ No password found")
            return

        def show_dialog():
            prompt = QDialog()
            prompt.setWindowTitle("Enter Password")
            layout = QVBoxLayout(prompt)
            layout.addWidget(QLabel("Enter your password:"))
            input_field = QLineEdit()
            input_field.setEchoMode(QLineEdit.Password)
            layout.addWidget(input_field)
            submit = QPushButton("OK")
            layout.addWidget(submit)
            submit.clicked.connect(prompt.accept)

            if prompt.exec_() == QDialog.Accepted:
                if check_password(input_field.text()):
                    print("✅ Password OK")
                    try:
                        print("🛫 Launching GUI subprocess")
                        subprocess.Popen(
                            [sys.executable, os.path.join(APP_DIR, "gui.py")],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True
                        )
                    except Exception as e:
                        print(f"[ERROR] Failed to launch GUI: {e}")
                        QMessageBox.critical(self.anchor, "Launch Error", f"Failed to open GUI: {e}")
                else:
                    print("❌ Password FAIL")
                    QMessageBox.warning(self.anchor, "Access Denied", "Incorrect password.")

        QTimer.singleShot(0, show_dialog)

    def run(self):
        print("[DEBUG] 🧠 Tray app starting...")
        exit_code = self.app.exec_()
        print(f"[DEBUG] 🔚 QApplication exited with code {exit_code}")
        sys.exit(exit_code)

    def handle_tray_click(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            print("🖱️ Tray icon clicked")
            self.toggle()

    def check_schedule(self):
        action = get_current_schedule_state()
        print(f"[DEBUG] 🕓 Schedule check: {action}")
        if action == "block" and not is_blocked():
            print("[DEBUG] Auto-blocking via schedule")
            block()
            self.update_icon()
        elif action == "unblock" and is_blocked():
            print("[DEBUG] Attempting schedule-based unblock — requires password")
            password, ok = QInputDialog.getText(
                self.anchor, "Unblock Required", "Enter your password to unblock:", QLineEdit.Password
            )
            if ok and check_password(password):
                print("[DEBUG] ✅ Password OK — auto-unblock allowed")
                unblock()
                self.update_icon()
            else:
                print("[DEBUG] ❌ Schedule unblock denied due to bad password or cancel")


# ✅ Main entrypoint — make sure QApplication is ready
if __name__ == "__main__":
    app = QApplication(sys.argv)  # Create first to avoid QWidget crash

    if is_first_run():
            first_run_setup()

            app_instance = FocusTrayApp()
            app_instance.run()

    if "--check" in sys.argv:
        action = get_current_schedule_state()
        print(f"[Manual Trigger] Schedule check: {action}")
        if action == "block" and not is_blocked():
            block()
        elif action == "unblock" and is_blocked():
            unblock()
        sys.exit()

    elif "--settings" in sys.argv:
        print("⚙️ --settings triggered")
        subprocess.Popen(
            [sys.executable, os.path.join(APP_DIR, "gui.py")],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        sys.exit()

    elif "--reset-password" in sys.argv:
        print("🔑 --reset-password triggered")
        reset_password_with_question()
        sys.exit()

    else:
        app_instance = FocusTrayApp()
        app_instance.run()
