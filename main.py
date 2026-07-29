#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import math
import json
import socket
import random
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

try:
    import audio
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

CONFIG_DIR = os.path.expanduser("~/.config/touch-grass-sim")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
IPC_PORT = 47382

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
    config = load_config()
    if config.get("setup_complete"):
        return True

    wizard_success = [False]
    root = tk.Tk()
    root.title("Touch Grass SIM — Setup Wizard")
    root.geometry("540x620")
    root.resizable(False, False)

    banner_path = get_asset_path("anime.png")
    if banner_path and PIL_AVAILABLE:
        try:
            pil_banner = Image.open(banner_path)
            pil_banner = ImageOps.fit(pil_banner, (540, 180), Image.Resampling.LANCZOS)
            banner_img_tk = ImageTk.PhotoImage(pil_banner)
            banner_label = tk.Label(root, image=banner_img_tk, bg="#1D2D44")
            banner_label.pack(fill="x")
        except Exception as e:
            log_msg(f"Failed to load anime.png banner: {e}")
            banner_path = None

    if not banner_path or not PIL_AVAILABLE:
        canvas = tk.Canvas(root, width=540, height=180, bg="#1D2D44", highlightthickness=0)
        canvas.pack(fill="x")
        canvas.create_rectangle(0, 0, 540, 100, fill="#3A5A40", outline="")
        canvas.create_text(270, 75, text="TOUCH GRASS SIM", fill="#F4F1DE", font=("Helvetica", 22, "bold"))

    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Welcome to Touch Grass SIM!", font=("Helvetica", 14, "bold")).pack(anchor="w", pady=(0, 5))
    
    desc_text = (
        "Touch Grass SIM enforces 5-minute mandatory digital wellness breaks every 4 hours.\n\n"
        "Features:\n"
        "• Animated Ghibli grass wave physics engine\n"
        "• Locked 300-second mindfulness break timer\n"
        "• Global shortcut (Ctrl + Alt + G) for early breaks\n"
        "• Environmental audio suppression\n"
    )
    ttk.Label(frame, text=desc_text, wraplength=480, justify="left").pack(anchor="w", pady=(0, 10))

    eula_frame = ttk.LabelFrame(frame, text="End User License Agreement", padding=10)
    eula_frame.pack(fill="both", expand=True, pady=(0, 10))

    eula_text = tk.Text(eula_frame, wrap="word", height=6, font=("Consolas", 8))
    eula_text.insert("1.0", "By using Touch Grass SIM, you agree to allow background hotkey listeners, system audio muting, and periodic break overlays designed to prevent digital fatigue. All data is processed entirely locally on your device.")
    eula_text.config(state="disabled")
    eula_text.pack(fill="both", expand=True)

    eula_var = tk.BooleanVar(value=False)

    def on_finish():
        save_config({"setup_complete": True, "eula_accepted": True})
        wizard_success[0] = True
        root.destroy()

    chk = tk.Checkbutton(frame, text="I agree to touch grass.", variable=eula_var, command=lambda: accept_btn.config(state=tk.NORMAL if eula_var.get() else tk.DISABLED))
    chk.pack(anchor="w", pady=(0, 15))

    btn_frame = tk.Frame(frame)
    btn_frame.pack(fill="x")

    # Switched to tk.Button to prevent blank button bug on macOS/Windows themes
    accept_btn = tk.Button(btn_frame, text="Accept & Continue", state=tk.DISABLED, command=on_finish, width=16)
    accept_btn.pack(side="right", padx=5)

    cancel_btn = tk.Button(btn_frame, text="Decline", command=root.destroy, width=10)
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
        self.root.bind("<Escape>", lambda e: "break")
        self.root.bind("<Alt-F4>", lambda e: "break")

        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()

        self.canvas = tk.Canvas(self.root, bg="#0B132B", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.ghibli_data = None
        self.init_ghibli_background()

        self.blades = []
        for _ in range(500):
            x = random.randint(0, self.width)
            h = random.randint(100, 240)
            color = random.choice(["#2D6A4F", "#40916C", "#52B788", "#74C69D", "#95D5B2", "#1B4332"])
            self.blades.append({"x": x, "h": h, "color": color, "phase": random.uniform(0, math.pi * 2)})

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
            activebackground="#059669",
            command=self.dismiss_overlay
        )
        self.return_btn.pack(padx=30, pady=(10, 20))

        self.setup_hotkey()
        self.start_ipc_server()
        
        self.animate()
        self.show_overlay()

    def init_ghibli_background(self):
        if not PIL_AVAILABLE:
            return
        img_path = get_asset_path("ghibli.png")
        if not img_path:
            return

        try:
            raw_img = Image.open(img_path)
            scaled_img = ImageOps.fit(raw_img, (self.width, self.height), Image.Resampling.LANCZOS)
            
            sky_height = int(self.height * 0.60)
            sky_crop = scaled_img.crop((0, 0, self.width, sky_height))
            sky_tk = ImageTk.PhotoImage(sky_crop)

            grass_crop = scaled_img.crop((0, sky_height, self.width, self.height))
            
            num_strips = 28
            strip_h = grass_crop.height // num_strips
            grass_strips = []

            for i in range(num_strips):
                sy = i * strip_h
                ey = (i + 1) * strip_h if i < num_strips - 1 else grass_crop.height
                strip_img = grass_crop.crop((0, sy, self.width, ey))
                strip_tk = ImageTk.PhotoImage(strip_img)
                grass_strips.append((strip_tk, sy + sky_height, (i + 1) / num_strips))

            self.ghibli_data = {"sky_tk": sky_tk, "grass_strips": grass_strips}
        except Exception as e:
            log_msg(f"Failed to process ghibli.png: {e}")

    def format_time(self, seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

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
            audio.start_wind_audio()
            
        self.update_timer()

    def dismiss_overlay(self):
        self.is_active = False
        self.root.withdraw()
        
        if AUDIO_AVAILABLE:
            audio.stop_wind_audio()
            
        # Schedule next automatic break in 4 hours
        self.root.after(14400000, self.show_overlay)

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
            
            # Organic math sway combining slow breeze and erratic flutter
            wind = (math.sin(t * 1.2) * 15) + (math.sin(t * 3.5) * 5)

            if self.ghibli_data:
                self.canvas.create_image(0, 0, image=self.ghibli_data["sky_tk"], anchor="nw")
                for strip_tk, y_pos, intensity in self.ghibli_data["grass_strips"]:
                    x_offset = math.sin(t * 1.6 + y_pos * 0.02) * (16.0 * intensity) + (wind * intensity)
                    self.canvas.create_image(x_offset, y_pos, image=strip_tk, anchor="nw")

                for blade in self.blades[::3]:
                    bx = blade["x"]
                    by = self.height
                    tip_x = bx + math.sin(t + blade["phase"]) * 14 + (wind * 0.5)
                    tip_y = by - (blade["h"] * 0.7)
                    self.canvas.create_line(bx, by, tip_x, tip_y, fill=blade["color"], width=2)
            else:
                self.canvas.create_rectangle(0, 0, self.width, self.height, fill="#0B132B", outline="")
                for blade in self.blades:
                    bx = blade["x"]
                    by = self.height
                    tip_x = bx + math.sin(t + blade["phase"]) * 18 + wind
                    tip_y = by - blade["h"]
                    self.canvas.create_line(bx, by, tip_x, tip_y, fill=blade["color"], width=4)

        self.root.after(33, self.animate)

    def setup_hotkey(self):
        if not PYNPUT_AVAILABLE:
            return
        def on_activate():
            log_msg("Hotkey triggered! Using root.after() to safely bridge to main UI thread...")
            self.root.after(0, self.show_overlay)
            
        try:
            self.hotkey_listener = keyboard.GlobalHotKeys({'<ctrl>+<alt>+g': on_activate})
            self.hotkey_listener.start()
            log_msg("Global hotkey listener registered.")
        except Exception as e:
            log_msg(f"Hotkey registration failed: {e}")

    def start_ipc_server(self):
        def server_loop():
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                server.bind(("127.0.0.1", IPC_PORT))
                server.listen(5)
                while True:
                    conn, _ = server.accept()
                    data = conn.recv(1024)
                    if b"TRIGGER_BREAK" in data:
                        log_msg("IPC trigger received. Routing to main thread.")
                        self.root.after(0, self.show_overlay)
                    conn.close()
            except Exception as e:
                log_msg(f"IPC Server error: {e}")
                
        threading.Thread(target=server_loop, daemon=True).start()

    def run(self):
        self.root.mainloop()

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
    try:
        log_msg("Starting Touch Grass SIM...")
        ensure_display_env()

        if try_notify_existing_instance():
            log_msg("Existing instance notified. Exiting duplicate process.")
            sys.exit(0)

        if not run_first_time_wizard():
            log_msg("Setup wizard skipped or declined.")
            sys.exit(0)

        app = AppManager(duration_sec=300)
        app.run()

    except Exception as e:
        crash_log = os.path.expanduser("~/touch_grass_crash.log")
        with open(crash_log, "w") as f:
            f.write("TOUCH GRASS SIM CRASH REPORT\n")
            f.write("="*30 + "\n")
            f.write(traceback.format_exc())
        sys.exit(1)