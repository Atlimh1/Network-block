# debug.py 🧠
# Universal debug logger for tray + subprocess crash tracing

import os
import sys
import atexit
import signal
import datetime
import logging

# 📁 Where the logs go
LOGFILE = os.path.expanduser("~/tray_debug.log")

# 🪵 Setup logging
logging.basicConfig(
    filename=LOGFILE,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

# 🖨️ Patch print to log too
def debug_print(*args, **kwargs):
    msg = " ".join(str(arg) for arg in args)
    logging.debug(msg)
    builtins_print = getattr(sys, '__stdout__', sys.stdout).write
    builtins_print(msg + "\n")

print = debug_print

# 🧼 Log app shutdown
atexit.register(lambda: print("🧨 [EXIT] Tray app shutting down."))

# 🛑 Trap kill signals (Linux)
def handle_sig(signum, frame):
    sig_map = {
        signal.SIGINT: "SIGINT",
        signal.SIGTERM: "SIGTERM"
    }
    print(f"🛑 [SIGNAL] Received {sig_map.get(signum, signum)} (signal {signum}) — terminating.")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_sig)
signal.signal(signal.SIGTERM, handle_sig)

# ✅ Init marker
print("✅ [DEBUG] Tray process started successfully.")
