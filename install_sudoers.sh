#!/bin/bash
# install_sudoers.sh

SUDOERS_LINE="ALL=(ALL) NOPASSWD: /usr/bin/cp /home/atli/Desktop/Block_python/hosts/hosts.blocked /etc/hosts, /usr/bin/cp /home/atli/Desktop/Block_python/hosts/hosts.clean /etc/hosts"
SUDOERS_FILE="/etc/sudoers.d/focusblocker"

USERNAME=$(logname)  # Get the actual GUI user

echo "$USERNAME $SUDOERS_LINE" > "$SUDOERS_FILE"
chmod 440 "$SUDOERS_FILE"
echo "[INSTALLER] ✅ Sudoers rule added for $USERNAME"
