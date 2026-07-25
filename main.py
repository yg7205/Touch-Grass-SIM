import os
import sys
import json
import time
import subprocess
import threading

# Cross-Platform User Configuration Path
if sys.platform == "win32":
    CONFIG_DIR = os.path.join(os.getenv("APPDATA", os.path.expanduser("~")), "TouchGrassSim")
elif sys.platform == "darwin":
    CONFIG_DIR = os.path.expanduser("~/Library/Application Support/TouchGrassSim")
else:
    CONFIG_DIR = os.path.expanduser("~/.config/touch-grass-sim")

CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

def show_gui_dialog(title, message, is_question=False):
    """Displays a native GUI popup dialog across Windows, macOS, and Linux."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()  # Hide main window
        root.attributes("-topmost", True)
        if is_question:
            res = messagebox.askyesno(title, message)
        else:
            messagebox.showinfo(title, message)
            res = True
        root.destroy()
        return res
    except Exception:
        # Fallback to Zenity on Linux if Tkinter is not available
        if sys.platform != "win32" and sys.platform != "darwin":
            env = os.environ.copy()
            cmd = ["zenity", "--question" if is_question else "--info", "--title", title, "--text", message, "--width", "400"]
            res = subprocess.run(cmd, env=env)
            return res.returncode == 0
        return True

def ensure_first_run_setup():
    """Runs setup wizard on first launch for all platforms without needing root/pkexec."""
    if os.path.exists(CONFIG_PATH):
        return  # Setup already completed!

    os.makedirs(CONFIG_DIR, exist_ok=True)

    # Launch GUI Setup Wizard
    tracking_enabled = show_gui_dialog(
        "Touch Grass SIM Setup Wizard",
        "Welcome to Touch Grass SIM!\n\nWould you like to enable activity tracking to help schedule breaks?",
        is_question=True
    )

    auth_key = f"TG-{os.urandom(8).hex()}"
    config_data = {
        "tracking_enabled": tracking_enabled,
        "auth_key": auth_key,
        "version": "1.0.0"
    }

    with open(CONFIG_PATH, "w") as f:
        json.dump(config_data, f, indent=2)

    show_gui_dialog(
        "Touch Grass SIM Ready!",
        f"Setup Complete!\n\nHotkey: Ctrl+Alt+G\nAuth Key: {auth_key}"
    )

def start_hotkey_listener():
    """Background listener for global hotkey Ctrl+Alt+G."""
    def listen():
        try:
            import keyboard
            keyboard.add_hotkey('ctrl+alt+g', lambda: show_gui_dialog("Touch Grass SIM", "Manual break triggered via hotkey!"))
            keyboard.wait()
        except Exception as e:
            print(f"Hotkey listener info: {e}")

    thread = threading.Thread(target=listen, daemon=True)
    thread.start()

def main():
    ensure_first_run_setup()
    start_hotkey_listener()

    print("Starting Touch Grass SIM desktop engine...")
    print("Listening for break triggers (Ctrl+Alt+G) and monitoring active window titles...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting Touch Grass SIM.")

if __name__ == "__main__":
    main()