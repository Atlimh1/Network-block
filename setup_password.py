from debug import print  # ⬅️ central debug logger

import os
import bcrypt
import json
import time
from PyQt5.QtWidgets import QInputDialog, QMessageBox, QLineEdit, QWidget

APP_DIR = "/home/atli/Desktop/Block_python"
PASSWORD_FILE = os.path.join(APP_DIR, "password.hash")
SECRET_QA_FILE = os.path.join(APP_DIR, "secret_qa.json")

# In-memory tracker for failed attempts
FAILED_ATTEMPTS = 0
MAX_ATTEMPTS = 3
LOCKOUT_SECONDS = 10
LAST_FAIL_TIME = 0


def ensure_password_exists(parent: QWidget = None) -> bool:
    """Checks if password file exists and prompts to create one if not."""
    if not os.path.exists(PASSWORD_FILE):
        print("[DEBUG] 🔐 Password file missing — prompting setup")
        QMessageBox.information(parent, "No Password",
            "Please set a password using the tray's 'Change Password' option.")
        return False
    return True


def check_password(password: str) -> bool:
    """Compares given password with stored hash using bcrypt."""
    global FAILED_ATTEMPTS, LAST_FAIL_TIME

    # Cooldown if too many failures
    if FAILED_ATTEMPTS >= MAX_ATTEMPTS:
        time_since = time.time() - LAST_FAIL_TIME
        if time_since < LOCKOUT_SECONDS:
            remaining = int(LOCKOUT_SECONDS - time_since)
            print(f"[DEBUG] ⏳ Too many attempts — cooldown {remaining}s remaining")
            return False
        else:
            print("[DEBUG] 🔄 Cooldown expired — resetting attempts")
            FAILED_ATTEMPTS = 0

    try:
        with open(PASSWORD_FILE, "rb") as f:
            stored_hash = f.read()

        if bcrypt.checkpw(password.encode(), stored_hash):
            print("[DEBUG] ✅ Password match")
            FAILED_ATTEMPTS = 0
            return True
        else:
            FAILED_ATTEMPTS += 1
            LAST_FAIL_TIME = time.time()
            print(f"[DEBUG] ❌ Password mismatch — failed attempts: {FAILED_ATTEMPTS}")
            return False
    except Exception as e:
        print(f"[ERROR] Exception during password check: {e}")
        return False


def reset_password_with_question(parent: QWidget = None):
    """Guided flow for resetting password using secret question."""
    try:
        if not isinstance(parent, QWidget):
            parent = None

        if not os.path.exists(SECRET_QA_FILE):
            print("[DEBUG] 🔐 Secret QA not set — entering setup mode")
            question, ok = QInputDialog.getText(
                parent, "Set Secret Question", "What is your recovery question?"
            )
            if not ok or not question.strip():
                print("[DEBUG] ❌ Secret question setup cancelled")
                return

            answer, ok = QInputDialog.getText(
                parent, "Set Answer", "What is the answer?", QLineEdit.Password
            )
            if not ok or not answer.strip():
                print("[DEBUG] ❌ Secret answer setup cancelled")
                return

            hashed_answer = bcrypt.hashpw(answer.encode(), bcrypt.gensalt())
            with open(SECRET_QA_FILE, "w") as f:
                json.dump({
                    "question": question.strip(),
                    "answer": hashed_answer.decode()
                }, f)

            print("[DEBUG] ✅ Secret QA saved")
            QMessageBox.information(parent, "Setup Complete",
                "You can now use this to reset your password.")
            return

        # ✅ Else: secret QA exists — do verification
        print("[DEBUG] 🔍 Secret QA found — entering reset flow")
        with open(SECRET_QA_FILE, "r") as f:
            data = json.load(f)

        user_answer, ok = QInputDialog.getText(
            parent, "Security Check", data["question"], QLineEdit.Password
        )
        if not ok or not user_answer.strip():
            print("[DEBUG] ❌ Secret QA answer cancelled")
            return

        stored_hash = data["answer"].encode()

        if bcrypt.checkpw(user_answer.encode(), stored_hash):
            print("[DEBUG] ✅ Secret QA verified")
            new_pass, ok = QInputDialog.getText(
                parent, "New Password", "Enter new password:", QLineEdit.Password
            )
            if ok and new_pass.strip():
                hashed_pass = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt())
                with open(PASSWORD_FILE, "wb") as f:
                    f.write(hashed_pass)
                print("[DEBUG] 🔑 Password successfully reset")
                QMessageBox.information(parent, "Password Changed", "Password updated successfully.")
            else:
                print("[DEBUG] ❌ New password not entered")
        else:
            print("[DEBUG] ❌ Secret QA failed")
            QMessageBox.warning(parent, "Wrong Answer", "Incorrect answer to secret question.")

    except Exception as e:
        print(f"[ERROR] Reset failed: {e}")
        QMessageBox.critical(parent, "Error", f"An error occurred: {str(e)}")

