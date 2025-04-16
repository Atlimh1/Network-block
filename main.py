import sys
import subprocess
import hashlib
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

def block():
    try:
        result = subprocess.run(["pkexec", "cp", BLOCKED_FILE, HOSTS_FILE])
        print("Block result:", result.returncode)
    except Exception as e:
        print("Failed to enable blocking:", e)

def unblock():
    try:
        result = subprocess.run(["pkexec", "cp", CLEAN_FILE, HOSTS_FILE])
        print("Unblock result:", result.returncode)
    except Exception as e:
        print("Failed to disable blocking:", e)


class FocusTrayApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.tray = QSystemTrayIcon()
        self.menu = QMenu()

        # Create tray actions
        self.toggle_action = QAction("Toggle Focus Mode")
        self.toggle_action.triggered.connect(self.toggle)

        self.quit_action = QAction("Quit")
        self.quit_action.triggered.connect(self.app.quit)

        self.menu.addAction(self.toggle_action)
        self.menu.addSeparator()
        self.menu.addAction(self.quit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.setToolTip("Focus Mode Toggle")
        self.update_icon()
        self.tray.show()

        # Auto-refresh icon every 5 seconds in case of external change
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_icon)
        self.timer.start(5000)

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

    def run(self):
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    app = FocusTrayApp()
    app.run()
