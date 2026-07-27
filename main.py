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
from tkinter.scrolledtext import ScrolledText

# Path configurations
CONFIG_DIR = os.path.expanduser("~/.config/touch-grass-sim")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
LOG_FILE = os.path.expanduser("~/.touch-grass-sim.log")
SOCKET_PORT = 47382  # Single instance IPC port

def log_error(msg):
    """Logs runtime errors for debugging."""
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def ensure_display_env():
    """Ensures DISPLAY variable is set for Linux GUI environments."""
    if sys.platform not in ("win32", "darwin") and "DISPLAY" not in os.environ:
        os.environ["DISPLAY"] = ":0"

# ==========================================
# GHIBLI-STYLE MEADOW & BREAK OVERLAY
# ==========================================

class GrassMeadowOverlay:
    def __init__(self, lock_time_sec=300):
        ensure_display_env()
        self.lock_time = lock_time_sec
        self.remaining_time = lock_time_sec
        self.wind_angle = 0.0

        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(bg="#DCEBFA")
        
        # Block window close and escape keys during mandatory break time
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.root.bind("<Escape>", lambda e: "break")

        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()

        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="#DCEBFA", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Generate Grass Blades
        self.blades = []
        num_blades = int(self.width / 3.5)
        palette = ["#2D5A27", "#4D8B43", "#6DA04B", "#87C059", "#A3D977", "#3B7A32"]
        
        for i in range(num_blades):
            x = random.randint(-20, self.width + 20)
            base_y = self.height + random.randint(0, 30)
            length = random.randint(140, 280)
            stiffness = random.uniform(0.5, 1.3)
            color = random.choice(palette)
            self.blades.append({
                "x": x,
                "y": base_y,
                "length": length,
                "stiffness": stiffness,
                "color": color,
                "offset": random.uniform(0, math.pi * 2)
            })

        # Generate Wildflowers (Daisies, Poppies, Buttercups, Clover)
        self.flowers = []
        flower_colors = ["#FFFFFF", "#E63946", "#FFD166", "#C77DFF"]
        for _ in range(70):
            fx = random.randint(50, self.width - 50)
            fy = random.randint(int(self.height * 0.65), self.height - 20)
            f_color = random.choice(flower_colors)
            f_size = random.randint(4, 8)
            self.flowers.append({"x": fx, "y": fy, "color": f_color, "size": f_size})

        # Generate Animated Butterflies
        self.butterflies = []
        for _ in range(4):
            self.butterflies.append({
                "x": random.randint(100, self.width - 100),
                "y": random.randint(int(self.height * 0.3), int(self.height * 0.6)),
                "dx": random.uniform(-1.5, 1.5),
                "dy": random.uniform(-0.8, 0.8),
                "wing_state": 0.0,
                "color": random.choice(["#FFB703", "#219EBC", "#FB8500"])
            })

        # Text Overlay Elements
        self.title_text = self.canvas.create_text(
            self.width / 2, self.height * 0.22,
            text="🌱 Touch Grass SIM",
            font=("Helvetica", 42, "bold"),
            fill="#1D3557"
        )
        self.timer_text = self.canvas.create_text(
            self.width / 2, self.height * 0.22 + 60,
            text="Take a deep breath and step away. Screen lock active...",
            font=("Helvetica", 18),
            fill="#457B9D"
        )

        self.close_btn_window = None

        # Start animation loops
        self.animate_frame()
        self.update_timer()
        self.root.mainloop()

    def animate_frame(self):
        """Main rendering loop: Grass, Path, Hills, Flowers, Butterflies."""
        self.canvas.delete("dynamic")
        self.wind_angle += 0.04
        wind_force = math.sin(self.wind_angle) * 30

        # 1. Draw Rolling Hills Background
        self.canvas.create_oval(
            -self.width * 0.2, self.height * 0.45,
            self.width * 0.8, self.height * 1.3,
            fill="#87C059", outline="", tags="dynamic"
        )
        self.canvas.create_oval(
            self.width * 0.2, self.height * 0.5,
            self.width * 1.3, self.height * 1.4,
            fill="#6DA04B", outline="", tags="dynamic"
        )

        # 2. Draw Dirt Trail Path
        path_points = [
            self.width * 0.45, self.height * 0.55,
            self.width * 0.48, self.height * 0.65,
            self.width * 0.52, self.height * 0.8,
            self.width * 0.6,  self.height
        ]
        self.canvas.create_line(
            path_points, fill="#D4A373", width=25, smooth=True, tags="dynamic"
        )

        # 3. Draw Swaying Grass Blades
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

        # 4. Draw Flowers
        for f in self.flowers:
            # Petals
            self.canvas.create_oval(
                f["x"] - f["size"], f["y"] - f["size"],
                f["x"] + f["size"], f["y"] + f["size"],
                fill=f["color"], outline="", tags="dynamic"
            )
            # Center core
            self.canvas.create_oval(
                f["x"] - 2, f["y"] - 2, f["x"] + 2, f["y"] + 2,
                fill="#FFD166", outline="", tags="dynamic"
            )

        # 5. Animate Butterflies
        for b in self.butterflies:
            b["x"] += b["dx"]
            b["y"] += b["dy"]
            b["wing_state"] += 0.3

            # Bounce off screen bounds
            if b["x"] < 50 or b["x"] > self.width - 50:
                b["dx"] *= -1
            if b["y"] < int(self.height * 0.2) or b["y"] > int(self.height * 0.7):
                b["dy"] *= -1

            wing_span = math.abs(math.sin(b["wing_state"])) * 8 + 2
            # Left wing
            self.canvas.create_oval(
                b["x"] - wing_span, b["y"] - 6, b["x"], b["y"] + 6,
                fill=b["color"], outline="", tags="dynamic"
            )
            # Right wing
            self.canvas.create_oval(
                b["x"], b["y"] - 6, b["x"] + wing_span, b["y"] + 6,
                fill=b["color"], outline="", tags="dynamic"
            )

        # Ensure text & buttons stay on top
        self.canvas.tag_raise(self.title_text)
        self.canvas.tag_raise(self.timer_text)
        if self.close_btn_window:
            self.canvas.tag_raise(self.close_btn_window)

        self.root.after(35, self.animate_frame)

    def update_timer(self):
        """Handles 5-minute unlock countdown and screen dimming."""
        if self.remaining_time > 0:
            mins, secs = divmod(self.remaining_time, 60)
            self.canvas.itemconfig(
                self.timer_text,
                text=f"Break in progress — Close button unlocks in {mins:02d}:{secs:02d}"
            )

            # Gradual Screen Dimming over 5 minutes
            dim_ratio = 1.0 - (self.remaining_time / self.lock_time)
            sky_r = int(220 - (100 * dim_ratio))
            sky_g = int(235 - (110 * dim_ratio))
            sky_b = int(250 - (120 * dim_ratio))
            bg_hex = f"#{sky_r:02x}{sky_g:02x}{sky_b:02x}"
            
            self.canvas.configure(bg=bg_hex)
            self.root.configure(bg=bg_hex)

            self.remaining_time -= 1
            self.root.after(1000, self.update_timer)
        else:
            self.canvas.itemconfig(self.timer_text, text="🌱 Break Complete! You may now return to your desktop.")
            self.show_close_button()

    def show_close_button(self):
        """Displays exit button after timer expires."""
        btn = tk.Button(
            self.root,
            text="Return to Desktop",
            font=("Helvetica", 14, "bold"),
            command=self.root.destroy,
            bg="#2D6A4F",
            fg="white",
            activebackground="#1B4332",
            activeforeground="white",
            padx=25,
            pady=12,
            relief="flat",
            cursor="hand2"
        )
        self.close_btn_window = self.canvas.create_window(
            self.width / 2, self.height * 0.22 + 130, window=btn
        )

def launch_overlay():
    """Safe invocation target for break overlay thread."""
    try:
        GrassMeadowOverlay(lock_time_sec=300)
    except Exception as e:
        log_error(f"Overlay crash: {e}\n{traceback.format_exc()}")

# ==========================================
# INSTALLER WIZARD & SETUP
# ==========================================

def run_background_system_setup(auth_key):
    """Saves system configurations locally."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        config_data = {"tracking_enabled": True, "auth_key": auth_key}
        with open(CONFIG_PATH, "w") as f:
            json.dump(config_data, f, indent=2)
    except Exception as e:
        log_error(f"Setup save error: {e}")

def run_first_time_wizard():
    """GUI setup installer wizard displayed ONLY on first launch."""
    if os.path.exists(CONFIG_PATH):
        return True  # Already installed! Skip wizard completely.

    wizard_completed = False
    ensure_display_env()

    try:
        root = tk.Tk()
        root.title("Touch Grass SIM — Setup Wizard")
        root.geometry("600x520")
        root.resizable(False, False)

        def on_install():
            nonlocal wizard_completed
            auth_key = f"TG-{os.urandom(8).hex()}"
            run_background_system_setup(auth_key)
            wizard_completed = True
            root.destroy()

        canvas = tk.Canvas(root, height=120, bg="#1B4332", highlightthickness=0)
        canvas.pack(fill="x", side="top")
        canvas.create_text(300, 45, text="🌱 Touch Grass SIM Setup", font=("Helvetica", 20, "bold"), fill="white")
        canvas.create_text(300, 80, text="Digital Wellness & Mindful Break Scheduler", font=("Helvetica", 10), fill="#D8F3DC")

        body = tk.Frame(root, padx=20, pady=15)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Software Agreement:", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        terms_box = ScrolledText(body, height=8, font=("Consolas", 9), wrap="word")
        terms_box.pack(fill="both", expand=True)
        terms_box.insert("1.0", (
            "TOUCH GRASS SIM AGREEMENT\n\n"
            "• App runs in the background to monitor long usage sessions.\n"
            "• Triggers a 5-minute non-interruptible meadow break screen.\n"
            "• Manual trigger available anytime via Ctrl + Alt + G.\n"
            "• All logs and settings remain strictly local (~/.config/touch-grass-sim/)."
        ))
        terms_box.configure(state="disabled")

        bottom = tk.Frame(root, padx=20, pady=15)
        bottom.pack(fill="x", side="bottom")

        agree_var = tk.BooleanVar(value=False)
        install_btn = tk.Button(
            bottom,
            text="Complete Setup & Enable Service",
            font=("Helvetica", 11, "bold"),
            fg="white",
            bg="#A0A0A0",
            state="disabled",
            command=on_install,
            pady=6
        )

        def toggle_button():
            if agree_var.get():
                install_btn.config(state="normal", bg="#2D6A4F")
            else:
                install_btn.config(state="disabled", bg="#A0A0A0")

        tk.Checkbutton(
            bottom, 
            text="I agree to enable automatic break enforcement", 
            variable=agree_var, 
            command=toggle_button
        ).pack(anchor="w", pady=(0, 10))
        
        install_btn.pack(fill="x")
        root.mainloop()

        return wizard_completed
    except Exception as e:
        log_error(f"Wizard error: {e}")
        return False

# ==========================================
# HOTKEY & BACKGROUND DAEMON
# ==========================================

def setup_global_hotkey():
    """Hooks Ctrl + Alt + G global shortcut."""
    try:
        from pynput import keyboard
        
        current_keys = set()

        def on_press(key):
            current_keys.add(key)
            has_ctrl = any(k in current_keys for k in [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r])
            has_alt = any(k in current_keys for k in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr])
            
            try:
                if has_ctrl and has_alt and hasattr(key, 'char') and key.char and key.char.lower() == 'g':
                    threading.Thread(target=launch_overlay, daemon=True).start()
            except AttributeError:
                pass

        def on_release(key):
            current_keys.discard(key)

        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
    except Exception as e:
        log_error(f"Pynput hotkey error: {e}")

def listen_for_ipc_triggers():
    """IPC server to trigger overlay when clicking desktop icon."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind(('127.0.0.1', SOCKET_PORT))
        server.listen(5)
        while True:
            conn, _ = server.accept()
            msg = conn.recv(1024).decode('utf-8')
            if msg == "TRIGGER":
                threading.Thread(target=launch_overlay, daemon=True).start()
            conn.close()
    except Exception as e:
        log_error(f"IPC Error: {e}")

def try_notify_existing_instance():
    """Notifies active daemon process if app icon is clicked."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', SOCKET_PORT))
        client.sendall(b"TRIGGER")
        client.close()
        return True
    except ConnectionRefusedError:
        return False

if __name__ == "__main__":
    try:
        # If app is ALREADY running in background, clicking icon opens break overlay
        if try_notify_existing_instance():
            sys.exit(0)

        # Run first-launch installer wizard if not yet configured
        if not run_first_time_wizard():
            sys.exit(0)

        # Start background listeners
        threading.Thread(target=listen_for_ipc_triggers, daemon=True).start()
        setup_global_hotkey()

        # Keep main background process alive
        while True:
            time.sleep(3600)
    except Exception as e:
        log_error(f"Main process crash: {e}\n{traceback.format_exc()}")