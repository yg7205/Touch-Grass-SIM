import time
import sys
import os
import json
import subprocess
import sys

CONFIG_DIR = "/etc/touch-grass-sim"
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

def ensure_first_run_setup():
    if os.path.exists(CONFIG_PATH):
        return  # Setup already completed!

    try:
        # Prompt user via Zenity (runs natively in the active desktop session)
        res = subprocess.run(
            [
                "zenity", "--question",
                "--title=Touch Grass SIM Setup Wizard",
                "--text=Welcome to Touch Grass SIM!\n\nWould you like to enable activity tracking to help schedule breaks?",
                "--width=400"
            ],
            capture_output=True
        )
        tracking_enabled = (res.returncode == 0)

        # Generate authentication key
        auth_key = f"TG-{os.urandom(8).hex()}"
        config_data = json.dumps({"tracking_enabled": tracking_enabled, "auth_key": auth_key})

        # Write config file to system directory using pkexec
        cmd = f"mkdir -p {CONFIG_DIR} && echo '{config_data}' > {CONFIG_PATH}"
        subprocess.run(["pkexec", "sh", "-c", cmd], check=True)

        # Show completion dialog
        subprocess.run([
            "zenity", "--info",
            "--title=Touch Grass SIM Ready!",
            f"--text=Setup Complete!\n\nHotkey: Ctrl+Alt+G\nAuth Key: {auth_key}",
            "--width=400"
        ])
    except Exception as e:
        print(f"Setup Wizard Error: {e}")

if __name__ == "__main__":
    ensure_first_run_setup()
    
def main():
    print("Starting Touch Grass SIM desktop engine...")
    print("Listening for break triggers and monitoring active window titles...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting Touch Grass SIM.")

if __name__ == "__main__":
    main()