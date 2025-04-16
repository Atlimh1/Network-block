# Network-block

A distraction-blocking system tray app with schedule-based filtering for Linux.

## 🚀 Features

- 🧠 **Focus Mode Toggle** — Quickly enable or disable blocking from the system tray
- ⏱️ **Schedule-Based Blocking** — Choose which hours of the day to block distracting websites
- 🔄 **Blacklist or Whitelist Mode** — Block only certain sites, or block everything *except* certain sites
- 🧰 **Hosts File Control** — Uses `/etc/hosts` to block access system-wide
- 🖼️ **PyQt5 GUI** — Clean interface to manage site lists and blocking schedule
- 🔒 **Protected Unblocking** — Unblocking requires password (via `pkexec`)

## 📸 Screenshots

> _(Add screenshots here of the GUI, tray icon, and schedule grid!)_

## 🛠 Installation

```bash
git clone https://github.com/atlimh1/Network-block.git
cd Network-block
pip install -r requirements.txt  # or manually install PyQt5

Make sure pkexec is installed and you can use it with elevated permissions:
sudo apt install policykit-1

python3 main.py
A tray icon will appear (😊 = blocking ON, 😠 = blocking OFF)

Right-click the icon to toggle focus mode or quit

Run gui.py to manage schedules and edit blocklists

Block_python/
├── gui.py               # Main GUI for settings/schedule
├── main.py              # Tray icon + toggle logic
├── schedule_widget.py   # Custom widget for visual scheduling
├── hosts/
│   ├── hosts.clean      # Whitelist version of /etc/hosts
│   └── hosts.blocked    # Blacklist version of /etc/hosts
├── settings.json        # Saved mode & schedule config
├── icons/               # PNG icons for tray and grid
└── logs/                # Toggle log file


📝 License

This software is free for personal and non-commercial use.

    For commercial use (including use in paid apps, services, or redistribution), a royalty-based license is required.
    Contact the author at [your-email@example.com] for licensing inquiries.

🙋 About
Created by atlimh1 as a minimalistic productivity tool.
