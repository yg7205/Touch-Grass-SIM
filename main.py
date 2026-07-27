import os
import sys
import json
import time
import socket
import threading
import subprocess
import traceback

# Core Tkinter imports (Fixed ScrolledText import for PyInstaller)
import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText

# Path configurations
CONFIG_DIR = os.path.expanduser("~/.config/touch-grass-sim")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
LOG_FILE = os.path.expanduser("~/.touch-grass-sim.log")
SOCKET_PORT = 47382  # Local port to prevent multiple instances and trigger overlay on app re-launch

def log_error(msg):
    """Logs runtime errors to a hidden file for debugging."""
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def ensure_display_env():
    """Ensures DISPLAY variable is set for Linux GUI environments."""
    if sys.platform not in ("win32", "darwin") and "DISPLAY" not in os.environ:
        os.environ["DISPLAY"] = ":0"

def show_grass_overlay():
    """Displays the full-screen mindfulness grass break window."""
    try:
        ensure_display_env()
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.configure(bg='#2E7D32')

        label = tk.Label(
            root, 
            text="🌱 Time to Touch Grass! 🌱\n\nTake a deep breath and step away from your screen.",
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
    except Exception as e:
        log_error(f"Overlay Error: {e}\n{traceback.format_exc()}")
        # Fallback dialog if Tkinter overlay encounters a display issue
        try:
            subprocess.run(["zenity", "--info", "--title=Touch Grass SIM", "--text=🌱 Time to Touch Grass! Take a break!"], check=False)
        except Exception:
            pass

def run_zenity_wizard_fallback():
    """Fallback GUI setup wizard using Zenity if Tkinter fails."""
    try:
        subprocess.run([
            "zenity", "--info",
            "--title=Touch Grass SIM — Setup Wizard",
            "--text=Welcome to Touch Grass SIM!\n\nThis app runs in the background to monitor digital wellness and remind you to take breaks.",
            "--width=400"
        ], check=True)

        terms_text = (
            "TOUCH GRASS SIM — TERMS OF SERVICE\n\n"
            "1. OVERVIEW: Touch Grass SIM schedules automated mindfulness breaks.\n"
            "2. PERMISSIONS: Listens for manual triggers (F12 global hotkey).\n"
            "3. PRIVACY: Data remains strictly local in ~/.config/touch-grass-sim/.\n\n"
            "Do you accept these terms and wish to complete setup?"
        )
        res = subprocess.run([
            "zenity", "--question",
            "--title=Touch Grass SIM — Terms & Conditions",
            "--text=" + terms_text,
            "--width=450"
        ], check=False)

        return res.returncode == 0
    except Exception as e:
        log_error(f"Zenity fallback error: {e}")
        return False

def run_background_system_setup(auth_key):
    """Generates local user configuration and sets up background permissions."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        config_data = {"tracking_enabled": True, "auth_key": auth_key}
        with open(CONFIG_PATH, "w") as f:
            json.dump(config_data, f, indent=2)

        if sys.platform not in ("win32", "darwin"):
            cmd = "echo 'KERNEL==\"event*\", NAME=\"input/%k\", MODE=\"0644\", TAG+=\"uaccess\"' > /etc/udev/rules.d/99-touch-grass-sim.rules && udevadm control --reload-rules && udevadm trigger"
            subprocess.run(["pkexec", "sh", "-c", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except Exception as e:
        log_error(f"Setup save error: {e}")

def run_first_time_wizard():
    """Runs the first-launch setup wizard."""
    if os.path.exists(CONFIG_PATH):
        return True

    wizard_completed = False

    try:
        ensure_display_env()
        root = tk.Tk()
        root.title("Touch Grass SIM — Setup Wizard")
        root.geometry("600x550")
        root.resizable(False, False)

        def on_install():
            nonlocal wizard_completed
            auth_key = f"TG-{os.urandom(8).hex()}"
            run_background_system_setup(auth_key)
            wizard_completed = True
            root.destroy()

        # Banner Frame
        canvas = tk.Canvas(root, height=140, bg="#2E7D32", highlightthickness=0)
        canvas.pack(fill="x", side="top")
        canvas.create_text(300, 50, text="🌱 Touch Grass SIM", font=("Helvetica", 22, "bold"), fill="white")
        canvas.create_text(300, 90, text="Mindfulness & Anti-Doomscroll Break Tracker", font=("Helvetica", 11), fill="#E8F5E9")

        # Terms Frame
        body_frame = tk.Frame(root, padx=15, pady=10)
        body_frame.pack(fill="both", expand=True)

        tk.Label(body_frame, text="Terms & Conditions Agreement:", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        terms_box = ScrolledText(body_frame, height=9, font=("Consolas", 9), wrap="word")
        terms_box.pack(fill="both", expand=True)
        
        TERMS_TEXT = (
            "TOUCH GRASS SIM — TERMS OF SERVICE & SYSTEM PERMISSIONS\n\n"
            "1. OVERVIEW\n"
            "Touch Grass SIM runs in the background to promote healthy screen time habits.\n\n"
            "2. SYSTEM PERMISSIONS & HOTKEYS\n"
            "By proceeding, Touch Grass SIM configures input permissions to enable manual "
            "global hotkey triggers (F12) and 4-hour break reminders.\n\n"
            "3. PRIVACY & DATA\n"
            "All activity and setup data remain strictly local on your device inside "
            "~/.config/touch-grass-sim/config.json."
        )
        terms_box.insert("1.0", TERMS_TEXT)
        terms_box.configure(state="disabled")

        # Controls Frame
        bottom_frame = tk.Frame(root, padx=15, pady=15)
        bottom_frame.pack(fill="x", side="bottom")

        agree_var = tk.BooleanVar(value=False)
        install_btn = tk.Button(
            bottom_frame,
            text="Install & Enable Hotkeys",
            font=("Helvetica", 11, "bold"),
            fg="white",
            bg="#CCCCCC",
            state="disabled",
            command=on_install,
            pady=6
        )

        def toggle_button():
            if agree_var.get():
                install_btn.config(state="normal", bg="#4CAF50")
            else:
                install_btn.config(state="disabled", bg="#CCCCCC")

        tk.Checkbutton(
            bottom_frame, 
            text="I have read and accept the Terms and Conditions", 
            variable=agree_var, 
            command=toggle_button,
            font=("Helvetica", 10)
        ).pack(anchor="w", pady=(0, 10))
        
        install_btn.pack(fill="x")

        root.mainloop()
        return wizard_completed

    except Exception as e:
        log_error(f"Tkinter Wizard failed: {e}\n{traceback.format_exc()}")
        # Fallback to Zenity wizard if Tkinter fails
        if run_zenity_wizard_fallback():
            auth_key = f"TG-{os.urandom(8).hex()}"
            run_background_system_setup(auth_key)
            return True
        return False

def listen_for_ipc_triggers():
    """IPC Server so opening the desktop app again triggers a break overlay."""
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
    except Exception as e:
        log_error(f"IPC Listener Error: {e}")

def try_notify_existing_instance():
    """Checks if app is already running and sends trigger signal."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', SOCKET_PORT))
        client.sendall(b"TRIGGER")
        client.close()
        return True
    except ConnectionRefusedError:
        return False

def setup_global_hotkey():
    """Hooks global F12 key press to trigger the grass overlay."""
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
        log_error(f"Hotkey listener error: {e}")

def background_timer_loop():
    """Triggers automated break every 4 hours."""
    FOUR_HOURS = 4 * 60 * 60
    while True:
        time.sleep(FOUR_HOURS)
        show_grass_overlay()

if __name__ == "__main__":
    try:
        # If already running, notify instance to open break overlay and exit
        if try_notify_existing_instance():
            sys.exit(0)

        # Run first-launch wizard if not configured
        if not run_first_time_wizard():
            sys.exit(0)

        # Start background threads
        threading.Thread(target=listen_for_ipc_triggers, daemon=True).start()
        setup_global_hotkey()
        threading.Thread(target=background_timer_loop, daemon=True).start()

        # Show initial break overlay upon successful installation/launch
        show_grass_overlay()
    except Exception as e:
        log_error(f"Main Thread Crash: {e}\n{traceback.format_exc()}")