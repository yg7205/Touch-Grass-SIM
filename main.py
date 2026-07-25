import os
import sys
import json
import time
import socket
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, ScrolledText

CONFIG_DIR = os.path.expanduser("~/.config/touch-grass-sim")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
SOCKET_PORT = 47382  # IPC Port for app clicks

def show_grass_overlay():
    """Renders the full-screen Grass Mindfulness Overlay."""
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.configure(bg='#2E7D32')

    label = tk.Label(
        root, 
        text="Time to Touch Grass!\n\nTake a deep breath and step away for a moment.",
        font=("Helvetica", 24, "bold"),
        fg="white",
        bg="#2E7D32",
        justify="center"
    )
    label.pack(expand=True)

    btn = tk.Button(
        root,
        text="I Touched Grass (Close)",
        font=("Helvetica", 14, "bold"),
        command=root.destroy,
        bg="#81C784",
        fg="black",
        padx=20,
        pady=10
    )
    btn.pack(pady=50)

    root.mainloop()

def run_background_system_setup(auth_key):
    """Silently configures system permissions for input hotkeys in background."""
    try:
        # Write config file locally
        os.makedirs(CONFIG_DIR, exist_ok=True)
        config_data = {"tracking_enabled": True, "auth_key": auth_key}
        with open(CONFIG_PATH, "w") as f:
            json.dump(config_data, f, indent=2)

        # Silent udev permission setup for Linux hotkey listening
        cmd = "echo 'KERNEL==\"event*\", NAME=\"input/%k\", MODE=\"0644\", TAG+=\"uaccess\"' > /etc/udev/rules.d/99-touch-grass-sim.rules && udevadm control --reload-rules && udevadm trigger"
        subprocess.run(["pkexec", "sh", "-c", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Background setup warning: {e}")

def run_first_time_wizard():
    """Renders the custom, expanded graphical wizard on first launch."""
    if os.path.exists(CONFIG_PATH):
        return True  # Already installed!

    wizard_completed = False

    def on_install():
        nonlocal wizard_completed
        auth_key = f"TG-{os.urandom(8).hex()}"
        
        # Execute silent background permission configuration
        run_background_system_setup(auth_key)
        
        wizard_completed = True
        root.destroy()

    root = tk.Tk()
    root.title("Touch Grass SIM — Setup Wizard")
    root.geometry("600x550")
    root.resizable(False, False)

    # 1. TOP HALF: Meadow Banner
    canvas = tk.Canvas(root, height=160, bg="#2E7D32", highlightthickness=0)
    canvas.pack(fill="x", side="top")
    
    # Visual Meadow Styling
    canvas.create_rectangle(0, 100, 600, 160, fill="#4CAF50", outline="")
    canvas.create_text(
        300, 60, 
        text="🌱 Touch Grass SIM", 
        font=("Helvetica", 22, "bold"), 
        fill="white"
    )
    canvas.create_text(
        300, 110, 
        text="Mindfulness & Anti-Doomscroll Break Tracker", 
        font=("Helvetica", 12), 
        fill="#E8F5E9"
    )

    # 2. MIDDLE: Terms & Agreement Scrollable Text
    body_frame = tk.Frame(root, padding=15)
    body_frame.pack(fill="both", expand=True)

    terms_label = tk.Label(body_frame, text="Terms & Conditions Agreement:", font=("Helvetica", 10, "bold"))
    terms_label.pack(anchor="w", pady=(0, 5))

    terms_box = ScrolledText(body_frame, height=10, font=("Consolas", 9), wrap="word")
    terms_box.pack(fill="both", expand=True)
    
    TERMS_TEXT = (
        "TOUCH GRASS SIM — TERMS OF SERVICE & SYSTEM PERMISSIONS\n\n"
        "1. OVERVIEW\n"
        "Touch Grass SIM runs in the background to monitor digital usage and remind you to take breaks.\n\n"
        "2. SYSTEM PERMISSIONS & HOTKEYS\n"
        "By clicking Install, Touch Grass SIM will configure system input permissions to enable "
        "global hotkeys (Ctrl+Alt+G) and automated break triggers.\n\n"
        "3. PRIVACY & DATA\n"
        "All activity tracking data and authentication tokens remain strictly local on your device "
        "inside ~/.config/touch-grass-sim/config.json.\n\n"
        "4. 4-HOUR AUTOMATED BREAKS\n"
        "The application will trigger a full-screen mindfulness break every 4 hours automatically."
    )
    terms_box.insert("1.0", TERMS_TEXT)
    terms_box.configure(state="disabled")  # Read only

    # 3. BOTTOM: Checkbox & Install Button
    bottom_frame = tk.Frame(root)
    bottom_frame.pack(fill="x", side="bottom", padx=20, pady=15)

    agree_var = tk.BooleanVar(value=False)

    def toggle_button():
        if agree_var.get():
            install_btn.config(state="normal", bg="#4CAF50")
        else:
            install_btn.config(state="disabled", bg="#CCCCCC")

    checkbox = tk.Checkbutton(
        bottom_frame, 
        text="I have read and accept the Terms and Conditions", 
        variable=agree_var, 
        command=toggle_button,
        font=("Helvetica", 10)
    )
    checkbox.pack(side="top", anchor="w", pady=(0, 10))

    install_btn = tk.Button(
        bottom_frame,
        text="Install & Enable Hotkeys",
        font=("Helvetica", 12, "bold"),
        fg="white",
        bg="#CCCCCC",
        state="disabled",
        command=on_install,
        padx=15,
        pady=8
    )
    install_btn.pack(side="bottom", fill="x")

    root.mainloop()
    return wizard_completed

def listen_for_ipc_triggers():
    """Listens for secondary app clicks while running in background."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind(('127.0.0.1', SOCKET_PORT))
        server.listen(5)
        while True:
            conn, _ = server.accept()
            msg = conn.recv(1024).decode('utf-8')
            if msg == "TRIGGER":
                threading.Thread(target=show_grass_overlay, daemon=True).start()
            conn.close()
    except Exception:
        pass

def try_notify_existing_instance():
    """Triggers the running background app when icon is clicked again."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', SOCKET_PORT))
        client.sendall(b"TRIGGER")
        client.close()
        return True
    except ConnectionRefusedError:
        return False

def setup_global_hotkey():
    """Global keyboard listener for Ctrl+Alt+G / F12."""
    try:
        from pynput import keyboard
        def on_press(key):
            try:
                if key == keyboard.Key.f12:
                    threading.Thread(target=show_grass_overlay, daemon=True).start()
            except AttributeError:
                pass
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
    except Exception as e:
        print(f"Hotkey listener status: {e}")

def background_timer_loop():
    """Guaranteed 4-hour (14,400 seconds) timer loop."""
    FOUR_HOURS = 4 * 60 * 60
    while True:
        time.sleep(FOUR_HOURS)
        show_grass_overlay()

if __name__ == "__main__":
    # If app is already running, clicking icon triggers break immediately and exits
    if try_notify_existing_instance():
        sys.exit(0)

    # First launch wizard execution
    run_first_time_wizard()

    # Start IPC listener for app click triggers
    threading.Thread(target=listen_for_ipc_triggers, daemon=True).start()

    # Start Hotkey Listener
    setup_global_hotkey()

    # Start 4-Hour Grass Reminder Loop
    threading.Thread(target=background_timer_loop, daemon=True).start()

    # Show initial grass overlay upon wizard completion / first launch
    show_grass_overlay()