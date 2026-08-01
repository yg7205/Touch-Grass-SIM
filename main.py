#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import math
import json
import socket
import select
import signal
import threading
import queue
import ctypes
import tkinter as tk
from tkinter import ttk

try:
    from PIL import Image, ImageTk, ImageOps
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

try:
    import audio
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

CONFIG_DIR = os.path.expanduser("~/.config/touch-grass-sim")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
IPC_PORT = 47382

EVENT_QUEUE = queue.Queue()
RUNNING_FLAG = threading.Event()
RUNNING_FLAG.set()

# FIX 1: Explicitly set Windows Taskbar AppUserModelID to prevent fallback to settings icon
if sys.platform == "win32":
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("touchgrass.sim.app.1.0")
    except Exception:
        pass

def log_msg(msg):
    print(f"[Touch Grass SIM] {msg}")

def ensure_display_env():
    if sys.platform.startswith("linux"):
        if "DISPLAY" not in os.environ:
            os.environ["DISPLAY"] = ":0"
        if "WAYLAND_DISPLAY" not in os.environ and os.path.exists("/run/user/1000/wayland-0"):
            os.environ["WAYLAND_DISPLAY"] = "wayland-0"

def get_asset_path(filename):
    search_paths = [
        os.path.join(os.path.dirname(__file__), filename),
        os.path.join(os.path.dirname(__file__), "assets", filename),
        os.path.expanduser(f"~/.config/touch-grass-sim/assets/{filename}"),
        f"/usr/share/touch-grass-sim/assets/{filename}"
    ]
    try:
        search_paths.insert(0, os.path.join(sys._MEIPASS, filename))
    except Exception:
        pass

    for path in search_paths:
        if os.path.exists(path):
            return path
    return None

def set_window_icon(window):
    icon_path = get_asset_path("icon.png")
    if icon_path and PIL_AVAILABLE:
        try:
            icon_img = Image.open(icon_path)
            icon_photo = ImageTk.PhotoImage(icon_img)
            window.iconphoto(True, icon_photo)
            window._icon_photo = icon_photo
        except Exception as e:
            log_msg(f"Icon load failed: {e}")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"setup_complete": False, "eula_accepted": False}

def save_config(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)

def run_first_time_wizard():
    wizard_success = [False]

    root = tk.Tk()
    root.title("Touch Grass SIM — Setup Wizard")
    root.geometry("540x620")
    root.resizable(False, False)
    set_window_icon(root)

    banner_path = get_asset_path("anime.png")
    if banner_path and PIL_AVAILABLE:
        try:
            pil_banner = Image.open(banner_path)
            pil_banner = ImageOps.fit(pil_banner, (540, 180), Image.Resampling.LANCZOS)
            banner_img_tk = ImageTk.PhotoImage(pil_banner)
            banner_label = tk.Label(root, image=banner_img_tk, bg="#1D2D44")
            banner_label.pack(fill="x")
            banner_label._img = banner_img_tk
        except Exception as e:
            log_msg(f"Banner load failed: {e}")

    frame = tk.Frame(root, bg="#1D2D44", padding=20) if hasattr(tk, 'padding') else tk.Frame(root, bg="#111827")
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="Welcome to Touch Grass SIM!", font=("Helvetica", 14, "bold"), fg="#95D5B2", bg="#111827").pack(anchor="w", padx=20, pady=(15, 5))

    desc_text = (
        "Touch Grass SIM enforces mandatory digital wellness breaks.\n\n"
        "Features:\n"
        "• Height-anchored Studio Ghibli grass sway engine\n"
        "• Locked 300-second mindfulness break timer\n"
        "• Global shortcut (Ctrl + Alt + G) for manual triggers\n"
        "• Environmental audio suppression\n"
    )
    tk.Label(frame, text=desc_text, font=("Helvetica", 10), fg="#E5E7EB", bg="#111827", justify="left").pack(anchor="w", padx=20, pady=(0, 10))

    eula_frame = tk.LabelFrame(frame, text=" Agreement ", font=("Helvetica", 9, "bold"), fg="#9CA3AF", bg="#111827", bd=1)
    eula_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    eula_text = tk.Text(eula_frame, wrap="word", height=5, font=("Consolas", 9), bg="#1F2937", fg="#D1D5DB", bd=0)
    eula_text.insert("1.0", "By continuing, you agree to allow background hotkey listeners, system audio muting, and periodic break overlays designed to prevent digital fatigue. All data remains 100% local.")
    eula_text.config(state="disabled")
    eula_text.pack(fill="both", expand=True, padx=5, pady=5)

    eula_var = tk.BooleanVar(value=False)

    def on_checkbox():
        if eula_var.get():
            accept_btn.config(state="normal", bg="#10B981", fg="#FFFFFF")
        else:
            accept_btn.config(state="disabled", bg="#374151", fg="#9CA3AF")

    chk = tk.Checkbutton(frame, text="I agree to touch grass.", variable=eula_var, command=on_checkbox, bg="#111827", fg="#F3F4F6", selectcolor="#1F2937", activebackground="#111827", activeforeground="#FFFFFF")
    chk.pack(anchor="w", padx=20, pady=(0, 15))

    btn_frame = tk.Frame(frame, bg="#111827")
    btn_frame.pack(fill="x", padx=20, pady=(0, 15))

    def on_finish():
        save_config({"setup_complete": True, "eula_accepted": True})
        wizard_success[0] = True
        root.destroy()

    accept_btn = tk.Button(btn_frame, text="Accept & Continue", state="disabled", bg="#374151", fg="#9CA3AF", font=("Helvetica", 10, "bold"), command=on_finish, relief="flat", padx=15, pady=6)
    accept_btn.pack(side="right", padx=5)

    cancel_btn = tk.Button(btn_frame, text="Decline", command=root.destroy, bg="#EF4444", fg="#FFFFFF", font=("Helvetica", 10, "bold"), relief="flat", padx=15, pady=6)
    cancel_btn.pack(side="right", padx=5)

    root.mainloop()
    return wizard_success[0]

class AppManager:
    def __init__(self, duration_sec=300):
        self.duration = duration_sec
        self.remaining = duration_sec
        self.is_active = False

        self.root = tk.Tk()
        self.root.title("Touch Grass SIM — Take a Break")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        set_window_icon(self.root)

        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()

        self.canvas = tk.Canvas(self.root, bg="#0B132B", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.ghibli_data = False
        self.init_ghibli_background()

        self.time_var = tk.StringVar(value=self.format_time(self.remaining))
        
        self.ui_frame = tk.Frame(self.root, bg="#111827", bd=2, relief="solid")
        self.ui_frame.place(relx=0.5, rely=0.15, anchor="center")

        tk.Label(self.ui_frame, text="TIME TO TOUCH GRASS", font=("Helvetica", 18, "bold"), fg="#95D5B2", bg="#111827").pack(padx=30, pady=(15, 5))
        tk.Label(self.ui_frame, textvariable=self.time_var, font=("Helvetica", 48, "bold"), fg="#FFFFFF", bg="#111827").pack(padx=30, pady=5)
        
        self.return_btn = tk.Button(
            self.ui_frame, 
            text="Return to Work (Locked)", 
            state="disabled", 
            font=("Helvetica", 12, "bold"), 
            bg="#374151", 
            fg="#9CA3AF", 
            command=self.dismiss_overlay
        )
        self.return_btn.pack(padx=30, pady=(10, 20))

        self.root.withdraw()
        self.poll_queue()
        self.animate()

    def init_ghibli_background(self):
        img_path = get_asset_path("ghibli.png")
        if not img_path or not PIL_AVAILABLE:
            return

        try:
            raw_img = Image.open(img_path)
            scaled_img = ImageOps.fit(raw_img, (self.width, self.height), Image.Resampling.LANCZOS)
            
            sky_height = int(self.height * 0.55)
            self.sky_tk = ImageTk.PhotoImage(scaled_img.crop((0, 0, self.width, sky_height)))

            grass_crop = scaled_img.crop((0, sky_height, self.width, self.height))
            
            num_strips = 32
            strip_h = grass_crop.height // num_strips
            self.grass_strips = []

            # Slice grass strips from top to bottom
            for i in range(num_strips):
                sy = i * strip_h
                ey = (i + 1) * strip_h if i < num_strips - 1 else grass_crop.height
                strip_tk = ImageTk.PhotoImage(grass_crop.crop((0, sy, self.width, ey)))
                
                # FIX 4: Height-anchored flexibility curve (Top of grass sways, roots stay grounded)
                flexibility = ((num_strips - i) / float(num_strips)) ** 1.8
                self.grass_strips.append((strip_tk, sy + sky_height, flexibility))

            self.ghibli_data = True
        except Exception as e:
            log_msg(f"Ghibli image processing failed: {e}")

    def format_time(self, seconds):
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def show_overlay(self):
        if self.is_active:
            return
        self.is_active = True
        self.remaining = self.duration
        self.start_time = time.time()
        self.return_btn.config(state="disabled", text="Return to Work (Locked)", bg="#374151", fg="#9CA3AF")
        
        self.root.deiconify()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.lift()
        
        if AUDIO_AVAILABLE:
            wind_file = get_asset_path("wind.mp3")
            audio.start_wind_audio(wind_file)
            
        self.update_timer()

    def dismiss_overlay(self):
        self.is_active = False
        self.root.withdraw()
        
        if AUDIO_AVAILABLE:
            audio.stop_wind_audio()

    def update_timer(self):
        if not self.is_active:
            return
        elapsed = int(time.time() - self.start_time)
        self.remaining = max(0, self.duration - elapsed)
        self.time_var.set(self.format_time(self.remaining))

        if self.remaining <= 0:
            self.return_btn.config(state="normal", text="Return to Work", bg="#10B981", fg="#FFFFFF")
        else:
            self.root.after(1000, self.update_timer)

    def animate(self):
        if self.is_active and self.root.winfo_exists():
            self.canvas.delete("all")
            t = time.time()
            
            # FIX 4: Organic dual-frequency wind equation
            breeze = math.sin(t * 1.2) * 18.0
            gust = math.sin(t * 3.4) * 6.0
            total_wind = breeze + gust

            if self.ghibli_data:
                self.canvas.create_image(0, 0, image=self.sky_tk, anchor="nw")
                for strip_tk, y_pos, flexibility in self.grass_strips:
                    x_offset = total_wind * flexibility
                    self.canvas.create_image(x_offset, y_pos, image=strip_tk, anchor="nw")

        self.root.after(33, self.animate)

    def poll_queue(self):
        try:
            while True:
                msg = EVENT_QUEUE.get_nowait()
                if msg == "TRIGGER_BREAK":
                    self.show_overlay()
        except queue.Empty:
            pass
        self.root.after(100, self.poll_queue)

    def run(self):
        self.root.mainloop()

def setup_global_hotkey():
    if not PYNPUT_AVAILABLE:
        return
    def on_activate():
        EVENT_QUEUE.put("TRIGGER_BREAK")
    try:
        hotkey = keyboard.GlobalHotKeys({'<ctrl>+<alt>+g': on_activate})
        t = threading.Thread(target=hotkey.start, daemon=True)
        t.start()
    except Exception as e:
        log_msg(f"Hotkey setup failed: {e}")

# FIX 3: Non-blocking IPC server so Python can exit cleanly on uninstall/close
def listen_for_ipc_triggers():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("127.0.0.1", IPC_PORT))
        server.listen(5)
        server.settimeout(1.0)
        
        while RUNNING_FLAG.is_set():
            try:
                conn, _ = server.accept()
                data = conn.recv(1024)
                if b"TRIGGER_BREAK" in data:
                    EVENT_QUEUE.put("TRIGGER_BREAK")
                conn.close()
            except socket.timeout:
                continue
    except Exception as e:
        log_msg(f"IPC Server closed: {e}")
    finally:
        server.close()

def try_notify_existing_instance():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(0.8)
        client.connect(("127.0.0.1", IPC_PORT))
        client.sendall(b"TRIGGER_BREAK\n")
        client.close()
        return True
    except Exception:
        return False

def clean_exit_handler(signum, frame):
    RUNNING_FLAG.clear()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, clean_exit_handler)
    signal.signal(signal.SIGTERM, clean_exit_handler)

    ensure_display_env()

    # Allow resetting config via CLI argument: python main.py --reset
    if "--reset" in sys.argv:
        if os.path.exists(CONFIG_PATH):
            os.remove(CONFIG_PATH)
            log_msg("Configuration reset successfully.")

    if try_notify_existing_instance():
        log_msg("Instance already running. Sent break signal to existing process.")
        sys.exit(0)

    # FIX 2: Check config state explicitly before proceeding
    config = load_config()
    if not config.get("setup_complete"):
        if not run_first_time_wizard():
            log_msg("Wizard declined or closed. Exiting.")
            sys.exit(0)

    threading.Thread(target=listen_for_ipc_triggers, daemon=True).start()
    setup_global_hotkey()

    app = AppManager(duration_sec=300)
    app.run()