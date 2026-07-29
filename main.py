import os
import sys
import time
import math
import json
import socket
import random
import threading
import tkinter as tk
from tkinter import ttk, messagebox

# Fallback import for global hotkey support
try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

CONFIG_DIR = os.path.expanduser("~/.config/touch-grass-sim")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
IPC_PORT = 47382

def log_msg(msg):
    print(f"[Touch Grass SIM] {msg}")

def ensure_display_env():
    """Ensure X11/Wayland display environment variables exist on Linux."""
    if sys.platform.startswith("linux"):
        if "DISPLAY" not in os.environ:
            os.environ["DISPLAY"] = ":0"
        if "WAYLAND_DISPLAY" not in os.environ and os.path.exists("/run/user/1000/wayland-0"):
            os.environ["WAYLAND_DISPLAY"] = "wayland-0"

# ==========================================
# 1. SETUP WIZARD & CONFIG MANAGEMENT
# ==========================================
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

    # Dynamic Canvas Header (Anime Mountain Vista)
    canvas = tk.Canvas(root, width=540, height=180, bg="#1D2D44", highlightthickness=0)
    canvas.pack(fill="x")

    # Sky Gradient
    canvas.create_rectangle(0, 0, 540, 100, fill="#3A5A40", outline="")
    canvas.create_rectangle(0, 100, 540, 180, fill="#588157", outline="")

    # Mountain Peaks
    canvas.create_polygon(0, 180, 120, 70, 240, 180, fill="#344E41", outline="")
    canvas.create_polygon(160, 180, 310, 50, 460, 180, fill="#2A3C24", outline="")
    canvas.create_polygon(340, 180, 440, 90, 540, 180, fill="#1B4332", outline="")

    # Header Title Text
    canvas.create_text(270, 75, text="TOUCH GRASS SIM", fill="#F4F1DE", font=("Helvetica", 22, "bold"))
    canvas.create_text(270, 110, text="Digital Wellness & Mindful Break Scheduler", fill="#A3B18A", font=("Helvetica", 11, "italic"))

    # Content Frame
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="Welcome to Touch Grass SIM!", font=("Helvetica", 14, "bold")).pack(anchor="w", pady=(0, 5))
    
    desc_text = (
        "Touch Grass SIM enforces 5-minute mandatory digital wellness breaks every 4 hours.\n\n"
        "Features:\n"
        "• Procedural grass and wildflower meadow simulation\n"
        "• Locked 300-second mindfulness break timer\n"
        "• Global shortcut (Ctrl + Alt + G) for early breaks\n"
        "• Cross-platform background service\n"
    )
    ttk.Label(frame, text=desc_text, wraplength=480, justify="left").pack(anchor="w", pady=(0, 10))

    # EULA Frame
    eula_frame = ttk.LabelFrame(frame, text="End User License Agreement", padding=10)
    eula_frame.pack(fill="both", expand=True, pady=(0, 10))

    eula_text = tk.Text(eula_frame, wrap="word", height=6, font=("Consolas", 8))
    eula_text.insert("1.0", "By using Touch Grass SIM, you agree to allow background hotkey listeners and periodic break overlays designed to prevent digital fatigue. All data is processed entirely locally on your device.")
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

# ==========================================
# 2. PROCEDURAL MEADOW BREAK OVERLAY
# ==========================================
class MeadowOverlay:
    def __init__(self, duration_sec=300):
        self.duration = duration_sec
        self.remaining = duration_sec

        self.root = tk.Tk()
        self.root.title("Touch Grass SIM — Take a Break")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)

        # Block close button and escape keys
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.root.bind("<Escape>", lambda e: "break")
        self.root.bind("<Alt-F4>", lambda e: "break")

        self.canvas = tk.Canvas(self.root, bg="#0B132B", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()

        # Generate Procedural Grass Blades
        self.blades = []
        for _ in range(600):
            x = random.randint(0, self.width)
            h = random.randint(120, 280)
            color = random.choice(["#2D6A4F", "#40916C", "#52B788", "#74C69D", "#95D5B2", "#1B4332"])
            self.blades.append({"x": x, "h": h, "color": color, "phase": random.uniform(0, math.pi * 2)})

        # Generate Wildflowers
        self.flowers = []
        for _ in range(45):
            fx = random.randint(0, self.width)
            fy = self.height - random.randint(40, 160)
            fcolor = random.choice(["#FFB703", "#FB8500", "#E63946", "#A8DADC", "#F4A261", "#E9C46A"])
            self.flowers.append({"x": fx, "y": fy, "color": fcolor})

        # Floating UI Controls
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
            command=self.root.destroy
        )
        self.return_btn.pack(padx=30, pady=(10, 20))

        self.start_time = time.time()
        self.animate()
        self.update_timer()

        self.root.mainloop()

    def format_time(self, seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02d}:{secs:02d}"

    def update_timer(self):
        elapsed = int(time.time() - self.start_time)
        self.remaining = max(0, self.duration - elapsed)
        self.time_var.set(self.format_time(self.remaining))

        if self.remaining <= 0:
            self.return_btn.config(state="normal", text="Return to Work", bg="#10B981", fg="#FFFFFF")
        else:
            self.root.after(1000, self.update_timer)

    def animate(self):
        if not self.root.winfo_exists():
            return

        self.canvas.delete("all")

        # Sky Gradient background
        self.canvas.create_rectangle(0, 0, self.width, self.height - 150, fill="#0B132B", outline="")
        self.canvas.create_rectangle(0, self.height - 250, self.width, self.height, fill="#1C2541", outline="")

        t = time.time() * 2.5
        wind = math.sin(t * 0.8) * 25

        # Render Swaying Grass
        for blade in self.blades:
            bx = blade["x"]
            by = self.height
            tip_x = bx + math.sin(t + blade["phase"]) * 18 + wind
            tip_y = by - blade["h"]
            
            self.canvas.create_line(bx, by, tip_x, tip_y, fill=blade["color"], width=4)

        # Render Wildflowers
        for flower in self.flowers:
            fx = flower["x"] + math.sin(t + flower["x"]) * 8
            fy = flower["y"]
            self.canvas.create_oval(fx - 6, fy - 6, fx + 6, fy + 6, fill=flower["color"], outline="")
            self.canvas.create_oval(fx - 2, fy - 2, fx + 2, fy + 2, fill="#FFFFFF", outline="")

        self.root.after(33, self.animate)

def launch_overlay():
    MeadowOverlay(duration_sec=300)

# ==========================================
# 3. BACKGROUND SERVICES & IPC LISTENERS
# ==========================================
def setup_global_hotkey():
    if not PYNPUT_AVAILABLE:
        log_msg("pynput not found — global hotkey disabled.")
        return

    def on_activate():
        log_msg("Global shortcut triggered (Ctrl + Alt + G). Launching overlay...")
        threading.Thread(target=launch_overlay, daemon=True).start()

    try:
        hotkey = keyboard.GlobalHotKeys({'<ctrl>+<alt>+g': on_activate})
        hotkey_thread = threading.Thread(target=hotkey.start, daemon=True)
        hotkey_thread.start()
        log_msg("Global hotkey registered: Ctrl + Alt + G")
    except Exception as e:
        log_msg(f"Failed to register global hotkey: {e}")

def listen_for_ipc_triggers():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("127.0.0.1", IPC_PORT))
        server.listen(5)
        log_msg(f"IPC Server listening on port {IPC_PORT}...")
        while True:
            conn, _ = server.accept()
            data = conn.recv(1024)
            if b"TRIGGER_BREAK" in data:
                log_msg("IPC trigger received. Opening break overlay...")
                threading.Thread(target=launch_overlay, daemon=True).start()
            conn.close()
    except Exception as e:
        log_msg(f"IPC Server warning: {e}")

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

# ==========================================
# 4. APPLICATION ENTRY POINT
# ==========================================
if __name__ == "__main__":
    log_msg("Starting Touch Grass SIM...")
    ensure_display_env()

    # Prevent duplicate runs
    if try_notify_existing_instance():
        log_msg("Existing instance notified. Exiting duplicate process.")
        sys.exit(0)

    # Launch onboarding setup wizard on first run
    if not run_first_time_wizard():
        log_msg("Setup wizard closed or declined. Exiting.")
        sys.exit(0)

    # Start background listeners
    threading.Thread(target=listen_for_ipc_triggers, daemon=True).start()
    setup_global_hotkey()

    # Launch initial break overlay
    launch_overlay()

    # 4-hour recurring schedule loop
    FOUR_HOURS = 4 * 60 * 60
    while True:
        time.sleep(FOUR_HOURS)
        launch_overlay()