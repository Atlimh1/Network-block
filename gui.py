from debug import print  # ✅ Enable centralized debug logging

import sys
import os
import json
import bcrypt
import subprocess
from setup_password import check_password, ensure_password_exists
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QGroupBox, QHBoxLayout, QCheckBox, QMessageBox, QInputDialog, QLineEdit
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QTimer, Qt
from schedule_widget import ScheduleGridWidget

APP_DIR = "/home/atli/Desktop/Block_python"
CLEAN_FILE = f"{APP_DIR}/hosts/hosts.clean"
BLOCKED_FILE = f"{APP_DIR}/hosts/hosts.blocked"
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        print("🧠 GUI Initialized")

        self.setWindowTitle("Focus Blocker Settings")
        self.setFixedSize(600, 400)
        self.load_settings()

        main_layout = QVBoxLayout()

        self.mode_button = QPushButton()
        self.mode_button.clicked.connect(self.toggle_mode)
        self.update_mode_button()
        main_layout.addWidget(self.mode_button)

        sites_group = QGroupBox("Site Lists")
        sites_layout = QHBoxLayout()
        self.whitelist_button = QPushButton("Edit Whitelist Sites")
        self.whitelist_button.setFixedSize(150, 40)
        self.blacklist_button = QPushButton("Edit Blacklist Sites")
        self.blacklist_button.setFixedSize(150, 40)
        self.whitelist_button.clicked.connect(self.edit_whitelist)
        self.blacklist_button.clicked.connect(self.edit_blacklist)
        sites_layout.addStretch()
        sites_layout.addWidget(self.whitelist_button)
        sites_layout.addWidget(self.blacklist_button)
        sites_layout.addStretch()
        sites_group.setLayout(sites_layout)
        main_layout.addWidget(sites_group)

        schedule_group = QGroupBox("Schedule")
        schedule_layout = QVBoxLayout()
        explanation_label = QLabel("Use the schedule to automatically block distractions at specific times.")
        schedule_layout.addWidget(explanation_label)

        self.enable_schedule = QCheckBox("Enable schedule blocking")
        self.enable_schedule.setChecked(self.schedule_enabled)
        schedule_layout.addWidget(self.enable_schedule)

        self.detailed_button = QPushButton("Edit Detailed Schedule")
        self.detailed_button.clicked.connect(self.open_detailed_schedule)
        schedule_layout.addWidget(self.detailed_button)

        schedule_group.setLayout(schedule_layout)
        main_layout.addWidget(schedule_group)

        self.change_password_button = QPushButton("Change Password")
        self.change_password_button.clicked.connect(self.change_password)
        main_layout.addWidget(self.change_password_button)

        self.setLayout(main_layout)

    def load_settings(self):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
            print("[DEBUG] ✅ Settings loaded")
        except FileNotFoundError:
            data = {}
            print("[DEBUG] ⚠️ Settings file not found, using defaults")

        self.mode = data.get("mode", "blacklist")
        self.schedule_enabled = data.get("schedule_enabled", False)
        self.schedule_data = data.get("schedule_data", {})

    def save_settings(self):
        data = {
            "mode": self.mode,
            "schedule_enabled": self.enable_schedule.isChecked(),
            "schedule_data": self.schedule_data
        }
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(data, f, indent=4)
            print("[DEBUG] 💾 Settings saved")
        except Exception as e:
            print(f"[ERROR] Failed to save settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def update_mode_button(self):
        next_mode = "Whitelist" if self.mode == "blacklist" else "Blacklist"
        self.mode_button.setText(f"Switch to {next_mode} Mode")

    def toggle_mode(self):
        self.mode = "whitelist" if self.mode == "blacklist" else "blacklist"
        print(f"[DEBUG] 🔁 Toggled mode → {self.mode}")
        self.update_mode_button()
        self.save_settings()

        try:
            print("[DEBUG] 🔄 Notifying tray to reload mode")
            subprocess.Popen(["python3", os.path.join(APP_DIR, "main.py"), "--check"])
        except Exception as e:
            print(f"[ERROR] Failed to notify tray: {e}")
            QMessageBox.critical(self, "Error", f"Failed to notify tray: {e}")

    def open_detailed_schedule(self):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton

        print(f"[DEBUG] 📅 Opening schedule editor for mode: {self.mode}")
        schedule = self.schedule_data.get(self.mode, {})

        dialog = QDialog(self)
        dialog.setWindowTitle("Detailed Schedule")
        dialog.setFixedSize(850, 430)

        layout = QVBoxLayout(dialog)

        # 🧠 Grid
        grid = ScheduleGridWidget(mode=self.mode)
        grid.set_schedule(schedule)
        layout.addWidget(grid)

        # 🧠 Legend row
        legend_layout = QHBoxLayout()

        # Full icon
        full_icon_label = QLabel()
        full_pixmap = QPixmap(os.path.join(APP_DIR, "icons/full.png"))
        full_icon_label.setPixmap(full_pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        full_icon_label.setFixedSize(22, 22)

        full_text = QLabel("= 60 minutes")
        full_text.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        # Half icon
        half_icon_label = QLabel()
        half_pixmap = QPixmap(os.path.join(APP_DIR, "icons/half.png"))
        half_icon_label.setPixmap(half_pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        half_icon_label.setFixedSize(22, 22)

        half_text = QLabel("= 30 minutes")
        half_text.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        # Add to layout with spacing
        legend_layout.addStretch()
        legend_layout.addWidget(full_icon_label)
        legend_layout.addSpacing(5)
        legend_layout.addWidget(full_text)
        legend_layout.addSpacing(40)
        legend_layout.addWidget(half_icon_label)
        legend_layout.addSpacing(5)
        legend_layout.addWidget(half_text)
        legend_layout.addStretch()

        layout.addLayout(legend_layout)


        # 🧠 Buttons row: Save, Clear, Close
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        clear_button = QPushButton("Clear All")
        close_button = QPushButton("Close")

        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(clear_button)
        button_layout.addWidget(close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        def on_save():
            updated_schedule = grid.get_schedule()
            self.schedule_data[self.mode] = updated_schedule
            self.save_settings()
            print("[DEBUG] ✅ Schedule saved")
            QMessageBox.information(self, "Saved", "Schedule updated successfully.")

        def on_clear():
            grid.clear_all()
            print("[DEBUG] 🧼 Schedule grid cleared")

        save_button.clicked.connect(on_save)
        clear_button.clicked.connect(on_clear)
        close_button.clicked.connect(dialog.accept)

        dialog.exec_()

    def edit_whitelist(self):
        print("[DEBUG] ✏️ Opening whitelist editor")
        try:
            subprocess.Popen(["xdg-open", CLEAN_FILE])
        except Exception as e:
            print(f"[ERROR] Failed to open whitelist: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open whitelist file:\n{e}")

    def edit_blacklist(self):
        print("[DEBUG] ✏️ Opening blacklist editor")
        try:
            subprocess.Popen(["xdg-open", BLOCKED_FILE])
        except Exception as e:
            print(f"[ERROR] Failed to open blacklist: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open blacklist file:\n{e}")

    def change_password(self):
        print("[DEBUG] 🔐 Begin password change flow")

        if not ensure_password_exists(self):
            print("[DEBUG] ❌ Password file missing")
            return

        current_pass, ok = QInputDialog.getText(
            self, "Current Password", "Enter current password:", QLineEdit.Password
        )
        if not ok or not current_pass.strip():
            print("[DEBUG] 🚫 Password input cancelled")
            return

        if not check_password(current_pass):
            print("[DEBUG] ❌ Current password incorrect")
            QMessageBox.warning(self, "Access Denied", "Incorrect current password.")
            return

        new_pass, ok = QInputDialog.getText(
            self, "New Password", "Enter new password:", QLineEdit.Password
        )
        if ok and new_pass.strip():
            try:
                hashed = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt())
                with open(os.path.join(APP_DIR, "password.hash"), "wb") as f:
                    f.write(hashed)
                print("[DEBUG] ✅ Password updated")
                QMessageBox.information(self, "Success", "Password updated.")
            except Exception as e:
                print(f"[ERROR] Failed to write password file: {e}")
                QMessageBox.critical(self, "Error", f"Failed to update password:\n{e}")
        else:
            print("[DEBUG] 🚫 New password entry cancelled")


if __name__ == "__main__":
    print("[DEBUG] 🚀 GUI booted via __main__")
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    exit_code = app.exec_()
    print(f"[DEBUG] 🧨 GUI exited with code {exit_code}")
    sys.exit(exit_code)
