#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import math
import json
import socket
import random
import queue
import threading
import traceback
import tkinter as tk
from tkinter import ttk, messagebox

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

CONFIG_DIR = os.path.expanduser("~/.config/touch-grass-sim")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
IPC_PORT = 47382

EVENT_QUEUE = queue.Queue()

def log_msg(msg):
    print(f"[Touch Grass SIM] {msg}")

def ensure_display_env():
    """Ensure X11/Wayland variables exist for Linux."""
    if sys.platform.startswith("linux"):
        if "DISPLAY" not in os.environ:
            os.environ["DISPLAY"] = ":0"
        if "WAYLAND_DISPLAY" not in os.environ and os.path.exists("/run/user/1000/wayland-0"):
            os.environ["WAYLAND_DISPLAY"] = "wayland-0"

def get_asset_path(filename):
    """Finds image files across local dev and installed package paths."""
    search_paths = [
        os.path.join(os.path.dirname(__file__), filename),
        os.path.join(os.path.dirname(__file__), "assets", filename),
        os.path.expanduser(f"~/.config/touch-grass-sim/assets/{filename}"),
        f"/usr/share/touch-grass-sim/assets/{filename}"
    ]
    for path in search_paths:
        if os.path.exists(path):
            return path
    return None

def set_window_icon(window):
    """Applies icon.png to the window titlebar and OS taskbar."""
    icon_path = get_asset_path("icon.png")
    if icon_path and PIL_AVAILABLE:
        try:
            icon_img = Image.open(icon_path)
            icon_photo = ImageTk.PhotoImage(icon_img)
            window.iconphoto(True, icon_photo)
            window._icon_photo = icon_photo  # Prevent garbage collection
        except Exception as e:
            log_msg(f"Could not load icon.png: {e}")

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
    """First-Time Wizard featuring anime.png banner."""
    config = load_config()
    if config.get("setup_complete"):
        return True

    wizard_success = [False]

    root = tk.Tk()
    root.title("Touch Grass SIM — Setup Wizard")
    root.geometry("540x620")
    root.resizable(False, False)
    set_window_icon(root)

    # Load anime.png banner
    banner_path = get_asset_path("anime.png")
    if banner_path and PIL_AVAILABLE:
        try:
            pil_banner = Image.open(banner_path)
            pil_banner = ImageOps.fit(pil_banner, (540, 180), Image.Resampling.LANCZOS)
            banner_img_tk = ImageTk.PhotoImage(pil_banner)
            banner_label = tk.Label(root, image=banner_img_tk, bg="#1D2D44")
            banner_label.image = banner_img_tk
            banner_label.pack(fill="x")
        except Exception as e:
            log_msg(f"Failed to load anime.png: {e}")
            banner_path = None

    if not banner_path or not PIL_AVAILABLE:
        canvas = tk.Canvas(root, width=540, height=180, bg="#1D2D44", highlightthickness=0)
        canvas.pack(fill="x")
        canvas.create_text(270, 90, text="TOUCH GRASS SIM", fill="#F4F1DE", font=("Helvetica", 22, "bold"))

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Welcome to Touch Grass SIM!", font=("Helvetica", 14, "bold")).pack(anchor="w", pady=(0, 5))
    
    desc_text = (
        "Touch Grass SIM enforces 5-minute mandatory digital wellness breaks every 4 hours.\n\n"
        "Features:\n"
        "• Animated Studio Ghibli grass physics engine\n"
        "• Locked 300-second mindfulness break timer\n"
        "• Global shortcut (Ctrl + Alt + G) for early breaks\n"
        "• Cross-platform background service\n"
    )
    ttk.Label(frame, text=desc_text, wraplength=480, justify="left").pack(anchor="w", pady=(0, 10))

    eula_frame = ttk.LabelFrame(frame, text="End User License Agreement", padding=10)
    eula_frame.pack(fill="both", expand=True, pady=(0, 10))

    eula_text = tk.Text(eula_frame, wrap="word", height=6, font=("Consolas", 8))
    eula_text.insert("1.0", "By using Touch Grass SIM, you agree to allow background hotkey listeners and periodic break overlays designed to prevent digital fatigue.")
    eula_text.config(state="disabled")
    eula_text.pack(fill="both", expand=True)

    eula_var = tk.BooleanVar(value=False)

    def on_finish():
        if not eula_var.get():
            messagebox.showwarning("EULA Required", "You must accept the EULA to proceed.")
            return
        save_config({"setup_complete": True, "eula_accepted": True})
        wizard_success[0] = True
        root.destroy()

    chk = ttk.Checkbutton(frame, text="I accept the End User License Agreement (EULA)", variable=eula_var)
    chk.pack(anchor="w", pady=(0, 15))

    btn_frame = ttk.Frame(frame)
    btn_frame.pack(fill="x")

    ttk.Button(btn_frame, text="Cancel", command=root.destroy).pack(side="right", padx=5)
    ttk.Button(btn_frame, text="Complete Setup", command=on_finish).pack(side="right")

    root.mainloop()
    return wizard_success[0]

class AppManager:
    """Main Break Overlay featuring ghibli.png physics."""
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

        self.ghibli_data = None
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

        self.poll_queue()
        self.animate()
        self.show_overlay()

    def init_ghibli_background(self):
        """Loads and slices ghibli.png for animation."""
        img_path = get_asset_path("ghibli.png")
        if not img_path or not PIL_AVAILABLE:
            log_msg("ghibli.png not found or PIL missing.")
            return

        try:
            raw_img = Image.open(img_path)
            scaled_img = ImageOps.fit(raw_img, (self.width, self.height), Image.Resampling.LANCZOS)
            
            sky_height = int(self.height * 0.60)
            self.sky_tk = ImageTk.PhotoImage(scaled_img.crop((0, 0, self.width, sky_height)))

            grass_crop = scaled_img.crop((0, sky_height, self.width, self.height))
            
            num_strips = 28
            strip_h = grass_crop.height // num_strips
            self.grass_strips = []

            for i in range(num_strips):
                sy = i * strip_h
                ey = (i + 1) * strip_h if i < num_strips - 1 else grass_crop.height
                strip_tk = ImageTk.PhotoImage(grass_crop.crop((0, sy, self.width, ey)))
                self.grass_strips.append((strip_tk, sy + sky_height, (i + 1) / num_strips))

            self.ghibli_data = True
        except Exception as e:
            log_msg(f"Failed to process ghibli.png: {e}")

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
        self.update_timer()

    def dismiss_overlay(self):
        self.is_active = False
        self.root.withdraw()
        self.root.after(14400000, self.show_overlay) # 4 hours

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
            t = time.time() * 2.5
            wind = math.sin(t * 0.8) * 20

            if self.ghibli_data:
                self.canvas.create_image(0, 0, image=self.sky_tk, anchor="nw")
                for strip_tk, y_pos, intensity in self.grass_strips:
                    x_offset = math.sin(t * 1.6 + y_pos * 0.02) * (16.0 * intensity) + (wind * intensity)
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
        log_msg("Pynput not found. Hotkey disabled.")
        return
    def on_activate():
        log_msg("Hotkey Ctrl+Alt+G pressed!")
        EVENT_QUEUE.put("TRIGGER_BREAK")
    try:
        hotkey = keyboard.GlobalHotKeys({'<ctrl>+<alt>+g': on_activate})
        threading.Thread(target=hotkey.start, daemon=True).start()
        log_msg("Hotkey listener active (Ctrl+Alt+G).")
    except Exception as e:
        log_msg(f"Hotkey failed: {e}")

def listen_for_ipc_triggers():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("127.0.0.1", IPC_PORT))
        server.listen(5)
        while True:
            conn, _ = server.accept()
            if b"TRIGGER_BREAK" in conn.recv(1024):
                EVENT_QUEUE.put("TRIGGER_BREAK")
            conn.close()
    except Exception as e:
        log_msg(f"IPC Server error: {e}")

def try_notify_existing_instance():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(1.0)
        client.connect(("127.0.0.1", IPC_PORT))
        client.sendall(b"TRIGGER_BREAK\n")
        client.close()
        return True
    except Exception:
        return False

if __name__ == "__main__":
    ensure_display_env()

    if try_notify_existing_instance():
        log_msg("Instance running. Triggered break. Exiting.")
        sys.exit(0)

    if not run_first_time_wizard():
        sys.exit(0)

    threading.Thread(target=listen_for_ipc_triggers, daemon=True).start()
    setup_global_hotkey()

    app = AppManager(duration_sec=300)
    app.run()