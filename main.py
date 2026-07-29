import os
import sys
import json
import time
import math
import random
import socket
import threading
import subprocess
import traceback

import tkinter as tk
from tkinter import ScrolledText

CONFIG_DIR = os.path.expanduser("~/.config/touch-grass-sim")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
LOG_FILE = os.path.expanduser("~/.touch-grass-sim.log")
SOCKET_PORT = 47382

def log_msg(msg):
    print(f"[TouchGrass] {msg}")
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def ensure_display_env():
    if sys.platform not in ("win32", "darwin"):
        if "DISPLAY" not in os.environ or not os.environ["DISPLAY"]:
            os.environ["DISPLAY"] = ":0"

ensure_display_env()

# ==========================================
# 1. ANIME SUNRISE MOUNTAIN VISTA (WIZARD HEADER)
# ==========================================

def draw_mountain_meadow_canvas(canvas, width, height, title_text="Touch Grass SIM Setup", subtitle_text="Digital Wellness & Mindful Break Scheduler"):
    canvas.delete("all")
    
    # Sky Gradient
    canvas.create_rectangle(0, 0, width, height * 0.45, fill="#D0E3F7", outline="")
    canvas.create_rectangle(0, height * 0.2, width, height * 0.45, fill="#FCEADE", outline="")

    # Sun
    sun_x, sun_y = width * 0.65, height * 0.25
    canvas.create_oval(sun_x - 22, sun_y - 22, sun_x + 22, sun_y + 22, fill="#FFF3B0", outline="")
    canvas.create_oval(sun_x - 12, sun_y - 12, sun_x + 12, sun_y + 12, fill="#FFFFFF", outline="")

    # Mountain Ranges
    mountains = [
        [0, height * 0.5, width * 0.25, height * 0.12, width * 0.45, height * 0.5],
        [width * 0.2, height * 0.5, width * 0.55, height * 0.08, width * 0.8, height * 0.5],
        [width * 0.6, height * 0.5, width * 0.85, height * 0.15, width, height * 0.5]
    ]
    for pts in mountains:
        canvas.create_polygon(pts, fill="#8E9AAF", outline="")
        snow_pts = [pts[2] - 20, pts[3] + 20, pts[2], pts[3], pts[2] + 20, pts[3] + 20]
        canvas.create_polygon(snow_pts, fill="#F8F9FA", outline="")

    # Pine Trees
    canvas.create_rectangle(0, height * 0.38, width, height * 0.5, fill="#E2ECE9", outline="")
    for tx in range(0, int(width), 10):
        th = random.randint(12, 25)
        canvas.create_polygon([tx, height * 0.5, tx + 5, height * 0.5 - th, tx + 10, height * 0.5], fill="#2D4A3E", outline="")

    # Hills
    canvas.create_oval(-width * 0.1, height * 0.45, width * 0.9, height * 1.3, fill="#95D5B2", outline="")
    canvas.create_oval(width * 0.1, height * 0.5, width * 1.2, height * 1.4, fill="#74C69D", outline="")

    # Scattered Flowers
    flower_colors = ["#7209B7", "#4361EE", "#F72585", "#FFB703", "#FFFFFF"]
    for _ in range(60):
        fx = random.randint(0, int(width))
        fy = random.randint(int(height * 0.58), int(height))
        fc = random.choice(flower_colors)
        if fc in ["#7209B7", "#4361EE"]:
            canvas.create_line(fx, fy, fx, fy - 10, fill="#2D6A4F", width=2)
            canvas.create_oval(fx - 2, fy - 14, fx + 2, fy - 6, fill=fc, outline="")
        else:
            canvas.create_oval(fx - 2, fy - 2, fx + 2, fy + 2, fill=fc, outline="")

    if title_text:
        canvas.create_text(width / 2, height * 0.32, text=title_text, font=("Helvetica", 16, "bold"), fill="#1A251C")
        canvas.create_text(width / 2, height * 0.62, text=subtitle_text, font=("Helvetica", 9, "bold"), fill="#1B4332")

# ==========================================
# 2. GHIBLI ANIMATED MEADOW OVERLAY
# ==========================================

class GrassMeadowOverlay:
    def __init__(self, lock_time_sec=300):
        log_msg("Spawning Ghibli Break Overlay...")
        self.lock_time = lock_time_sec
        self.remaining_time = lock_time_sec
        self.wind_angle = 0.0

        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(bg="#DCEBFA")

        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.root.bind("<Escape>", lambda e: "break")

        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()

        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="#DCEBFA", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.blades = []
        num_blades = int(self.width / 3.5)
        palette = ["#2D5A27", "#4D8B43", "#6DA04B", "#87C059", "#A3D977", "#3B7A32"]
        for _ in range(num_blades):
            self.blades.append({
                "x": random.randint(-20, self.width + 20),
                "y": self.height + random.randint(0, 30),
                "length": random.randint(140, 280),
                "stiffness": random.uniform(0.5, 1.3),
                "color": random.choice(palette),
                "offset": random.uniform(0, math.pi * 2)
            })

        self.flowers = []
        flower_colors = ["#7209B7", "#4361EE", "#F72585", "#FFB703", "#FFFFFF", "#E63946"]
        for _ in range(90):
            self.flowers.append({
                "x": random.randint(30, self.width - 30),
                "y": random.randint(int(self.height * 0.62), self.height - 10),
                "color": random.choice(flower_colors),
                "size": random.randint(4, 8)
            })

        self.title_text = self.canvas.create_text(
            self.width / 2, self.height * 0.22,
            text="Touch Grass SIM", font=("Helvetica", 38, "bold"), fill="#1D3557"
        )
        self.timer_text = self.canvas.create_text(
            self.width / 2, self.height * 0.22 + 50,
            text="Take a deep breath and step away. Break active...",
            font=("Helvetica", 16), fill="#457B9D"
        )

        self.close_btn_window = None
        self.animate_frame()
        self.update_timer()

        self.root.lift()
        self.root.focus_force()
        self.root.mainloop()

    def animate_frame(self):
        self.canvas.delete("dynamic")
        self.wind_angle += 0.04
        wind_force = math.sin(self.wind_angle) * 30

        draw_mountain_meadow_canvas(self.canvas, self.width, self.height, title_text="", subtitle_text="")

        for b in self.blades:
            sway = math.sin(self.wind_angle * b["stiffness"] + b["offset"]) * wind_force
            tip_x = b["x"] + sway
            tip_y = b["y"] - b["length"]
            ctrl_x = b["x"] + (sway * 0.5)
            ctrl_y = b["y"] - (b["length"] * 0.5)

            self.canvas.create_line(
                b["x"], b["y"], ctrl_x, ctrl_y, tip_x, tip_y,
                fill=b["color"], width=3, smooth=True, tags="dynamic"
            )

        for f in self.flowers:
            if f["color"] in ["#7209B7", "#4361EE"]:
                self.canvas.create_line(f["x"], f["y"], f["x"], f["y"] - 18, fill="#2D6A4F", width=3, tags="dynamic")
                self.canvas.create_oval(f["x"] - 4, f["y"] - 22, f["x"] + 4, f["y"] - 8, fill=f["color"], outline="", tags="dynamic")
            else:
                self.canvas.create_oval(f["x"] - f["size"], f["y"] - f["size"], f["x"] + f["size"], f["y"] + f["size"], fill=f["color"], outline="", tags="dynamic")

        self.canvas.tag_raise(self.title_text)
        self.canvas.tag_raise(self.timer_text)
        if self.close_btn_window:
            self.canvas.tag_raise(self.close_btn_window)

        self.root.after(35, self.animate_frame)

    def update_timer(self):
        if self.remaining_time > 0:
            mins, secs = divmod(self.remaining_time, 60)
            self.canvas.itemconfig(self.timer_text, text=f"Break in progress — Return button unlocks in {mins:02d}:{secs:02d}")
            self.remaining_time -= 1
            self.root.after(1000, self.update_timer)
        else:
            self.canvas.itemconfig(self.timer_text, text="Break Complete! You may now return to your desktop.")
            self.show_close_button()

    def show_close_button(self):
        btn = tk.Button(
            self.root, text="Return to Desktop", font=("Helvetica", 14, "bold"),
            command=self.root.destroy, bg="#2D6A4F", fg="white",
            activebackground="#1B4332", activeforeground="white",
            padx=25, pady=10, relief="flat", cursor="hand2"
        )
        self.close_btn_window = self.canvas.create_window(self.width / 2, self.height * 0.22 + 120, window=btn)

def launch_overlay():
    try:
        GrassMeadowOverlay(lock_time_sec=300)
    except Exception as e:
        log_msg(f"Overlay crash: {e}\n{traceback.format_exc()}")

# ==========================================
# 3. WIZARD INSTALLER WITH EULA
# ==========================================

def run_background_system_setup(auth_key):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        config_data = {"tracking_enabled": True, "auth_key": auth_key}
        with open(CONFIG_PATH, "w") as f:
            json.dump(config_data, f, indent=2)
        log_msg("Configuration file created.")
    except Exception as e:
        log_msg(f"Setup configuration error: {e}")

def run_first_time_wizard():
    if os.path.exists(CONFIG_PATH):
        log_msg("Config present. Skipping setup wizard.")
        return True

    log_msg("Displaying Setup Wizard...")
    wizard_completed = False

    try:
        root = tk.Tk()
        root.title("Touch Grass SIM — Setup Wizard")
        root.geometry("640x560")
        root.resizable(False, False)

        def on_install():
            nonlocal wizard_completed
            auth_key = f"TG-{os.urandom(8).hex()}"
            run_background_system_setup(auth_key)
            wizard_completed = True
            root.destroy()

        header_canvas = tk.Canvas(root, height=160, bg="#DCEBFA", highlightthickness=0)
        header_canvas.pack(fill="x", side="top")
        draw_mountain_meadow_canvas(header_canvas, 640, 160)

        body = tk.Frame(root, padx=20, pady=10)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="End-User License & Terms of Service Agreement:", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        terms_box = ScrolledText(body, height=10, font=("Consolas", 9), wrap="word")
        terms_box.pack(fill="both", expand=True)
        
        EULA_TEXT = (
            "TOUCH GRASS SIM — END-USER LICENSE AGREEMENT & TERMS OF SERVICE\n\n"
            "1. PURPOSE & DIGITAL WELLNESS SERVICE\n"
            "Touch Grass SIM is designed to promote physical breaks and digital health. By installing "
            "this application, you authorize Touch Grass SIM to run a local background process "
            "to schedule and trigger mandatory mindfulness sessions.\n\n"
            "2. SYSTEM LOCK ENFORCEMENT & MANDATORY BREAKS\n"
            "During an active break session (every 4 hours or manually via Ctrl+Alt+G), the app will render "
            "a full-screen overlay for 300 seconds (5 minutes). Non-essential window controls are restricted "
            "until the session timer expires.\n\n"
            "3. GLOBAL HOTKEYS & PERMISSIONS\n"
            "The app registers a background system shortcut listener (Ctrl + Alt + G). All event monitoring "
            "is kept local to your machine. No screen data, keystrokes, or personal details leave your device.\n\n"
            "4. PRIVACY & LOCAL CONFIGURATION\n"
            "All software configuration, authentication tokens, and application logs are stored strictly inside "
            "your user directory (~/.config/touch-grass-sim/).\n\n"
            "5. NO WARRANTY & LIABILITY\n"
            "The software is provided 'as-is' without warranty of any kind."
        )
        terms_box.insert("1.0", EULA_TEXT)
        terms_box.configure(state="disabled")

        bottom = tk.Frame(root, padx=20, pady=12)
        bottom.pack(fill="x", side="bottom")

        agree_var = tk.BooleanVar(value=False)
        install_btn = tk.Button(
            bottom,
            text="Install & Enable Hotkey Service",
            font=("Helvetica", 11, "bold"),
            fg="white",
            bg="#A0A0A0",
            state="disabled",
            command=on_install,
            pady=8
        )

        def toggle_button():
            if agree_var.get():
                install_btn.config(state="normal", bg="#2D6A4F")
            else:
                install_btn.config(state="disabled", bg="#A0A0A0")

        tk.Checkbutton(
            bottom, 
            text="I accept the Terms of Service and enable automatic break triggers", 
            variable=agree_var, 
            command=toggle_button
        ).pack(anchor="w", pady=(0, 8))
        
        install_btn.pack(fill="x")
        
        root.lift()
        root.focus_force()
        root.mainloop()

        return wizard_completed
    except Exception as e:
        log_msg(f"Wizard error: {e}\n{traceback.format_exc()}")
        return False

# ==========================================
# 4. HOTKEY & IPC LISTENERS
# ==========================================

def setup_global_hotkey():
    def hotkey_loop():
        try:
            from pynput import keyboard
            current_keys = set()

            def on_press(key):
                current_keys.add(key)
                has_ctrl = any(k in current_keys for k in [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r])
                has_alt = any(k in current_keys for k in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr])
                
                try:
                    if has_ctrl and has_alt and hasattr(key, 'char') and key.char and key.char.lower() == 'g':
                        log_msg("Hotkey Ctrl+Alt+G pressed! Triggering overlay...")
                        threading.Thread(target=launch_overlay, daemon=True).start()
                except AttributeError:
                    pass

            def on_release(key):
                current_keys.discard(key)

            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                listener.join()
        except Exception as e:
            log_msg(f"Hotkey listener error: {e}")

    threading.Thread(target=hotkey_loop, daemon=True).start()

def listen_for_ipc_triggers():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(('127.0.0.1', SOCKET_PORT))
        server.listen(5)
        log_msg(f"IPC Server running on port {SOCKET_PORT}.")
        while True:
            conn, _ = server.accept()
            msg = conn.recv(1024).decode('utf-8')
            if msg == "TRIGGER":
                log_msg("IPC trigger received. Forcing overlay UI...")
                threading.Thread(target=launch_overlay, daemon=True).start()
            conn.close()
    except Exception as e:
        log_msg(f"IPC Server Error: {e}")

def try_notify_existing_instance():
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(1.0)
        client.connect(('127.0.0.1', SOCKET_PORT))
        client.sendall(b"TRIGGER")
        client.close()
        log_msg("Notified active background process via IPC.")
        return True
    except (ConnectionRefusedError, OSError, socket.timeout):
        return False

if __name__ == "__main__":
    log_msg("Starting application launcher...")

    if try_notify_existing_instance():
        sys.exit(0)

    if not run_first_time_wizard():
        log_msg("Setup wizard canceled. Exiting.")
        sys.exit(0)

    threading.Thread(target=listen_for_ipc_triggers, daemon=True).start()
    setup_global_hotkey()

    launch_overlay()

    FOUR_HOURS = 4 * 60 * 60
    while True:
        time.sleep(FOUR_HOURS)
        launch_overlay()