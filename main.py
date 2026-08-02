#!/usr/bin/env python3
import os
import sys
import time
import math
import json
import socket
import threading
import queue
import tkinter as tk

try:
    from PIL import Image, ImageTk, ImageOps
except ImportError:
    pass

try:
    from pynput import keyboard
except ImportError:
    pass

try:
    import audio
except ImportError:
    pass

CONFIG_PATH = os.path.expanduser("~/.config/touch-grass-sim/config.json")
IPC_PORT = 47382
EVENT_QUEUE = queue.Queue()

# --- UNINSTALLER: ORPHAN FILE CLEANUP ---
if "--uninstall" in sys.argv:
    if os.path.exists(CONFIG_PATH):
        os.remove(CONFIG_PATH)
    sys.exit(0)

# --- FORCE WIZARD TO LOAD ---
# This wipes out any old test configurations so the wizard is forced to show.
if os.path.exists(CONFIG_PATH):
    try: 
        os.remove(CONFIG_PATH)
    except Exception: 
        pass

def get_asset_path(filename):
    return os.path.join(os.path.dirname(__file__), "assets", filename)

def set_window_icon(window):
    # 1. LINUX LOGO FIX
    try: 
        window.wm_class("touch-grass-sim", "Touch Grass SIM")
    except Exception: 
        pass
    
    # 2. WINDOWS LOGO FIX
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("touchgrass.sim.app.1.0")
        except Exception: 
            pass
            
    # 3. APPLY ICON
    try:
        icon_img = ImageTk.PhotoImage(Image.open(get_asset_path("icon.png")))
        window.iconphoto(True, icon_img)
        window._icon_photo = icon_img
    except Exception: 
        pass

def run_wizard():
    root = tk.Tk()
    root.title("Touch Grass SIM Setup")
    root.geometry("540x600")
    root.configure(bg="#2D3748")
    
    # Apply the logo fix to the wizard
    set_window_icon(root)

    canvas = tk.Canvas(root, width=540, height=180, bg="#1D2D44", highlightthickness=0)
    canvas.pack(fill="x")
    
    try:
        pil_banner = Image.open(get_asset_path("anime.png"))
        pil_banner = ImageOps.fit(pil_banner, (540, 180), Image.Resampling.LANCZOS)
        banner_img = ImageTk.PhotoImage(pil_banner)
        canvas.create_image(0, 0, image=banner_img, anchor="nw")
        canvas.image = banner_img 
    except Exception:
        canvas.create_text(270, 90, text="TOUCH GRASS SIM", fill="#F4F1DE", font=("Helvetica", 22, "bold"))
    
    btn_frame = tk.Frame(root, bg="#2D3748")
    btn_frame.pack(side="bottom", pady=40)
    
    def on_accept():
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump({"setup_complete": True}, f)
        root.destroy()
        
    accept_btn = tk.Button(btn_frame, text="I Agree - Continue", command=on_accept, bg="#48BB78", fg="black", padx=10, pady=5)
    accept_btn.pack(side="left", padx=10)
    
    root.mainloop()
    return os.path.exists(CONFIG_PATH)

class AppManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() # Hide the background engine window
        self.overlay = None
        self.check_queue()

    def check_queue(self):
        try:
            while True:
                msg = EVENT_QUEUE.get_nowait()
                if msg == "TRIGGER" and self.overlay is None:
                    self.show_overlay()
        except queue.Empty:
            pass
        self.root.after(100, self.check_queue)

    def show_overlay(self):
        try:
            audio.mute_system_audio()
            audio.start_wind_audio(get_asset_path("wind.mp3"))
        except Exception: 
            pass

        self.overlay = tk.Toplevel(self.root)
        self.overlay.attributes("-fullscreen", True)
        self.overlay.attributes("-topmost", True)
        self.overlay.configure(bg="#0B132B")
        
        # Apply the logo fix to the break screen
        set_window_icon(self.overlay)

        canvas = tk.Canvas(self.overlay, bg="#0B132B", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        try:
            self.sky_img = ImageTk.PhotoImage(Image.open(get_asset_path("sky.png")))
            self.grass_img = ImageTk.PhotoImage(Image.open(get_asset_path("ghibli.png")))
            
            def animate():
                if not self.overlay or not self.overlay.winfo_exists(): return
                canvas.delete("all")
                canvas.create_image(0, 0, image=self.sky_img, anchor="nw")
                sway = math.sin(time.time() * 1.5) * 20
                canvas.create_image(-50 + sway, 500, image=self.grass_img, anchor="nw")
                self.overlay.after(33, animate)
            animate()
        except Exception: 
            pass

        def on_close():
            try:
                audio.stop_wind_audio()
                audio.unmute_system_audio()
            except Exception: 
                pass
            self.overlay.destroy()
            self.overlay = None

        tk.Button(self.overlay, text="Return to Work", command=on_close, bg="#48BB78", fg="black", font=("Helvetica", 14, "bold")).place(relx=0.5, rely=0.5, anchor="center")

def on_hotkey():
    EVENT_QUEUE.put("TRIGGER")

def listen_ipc():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("127.0.0.1", IPC_PORT))
        server.listen(1)
        while True:
            server.accept()
            EVENT_QUEUE.put("TRIGGER")
    except Exception:
        pass

if __name__ == "__main__":
    if not run_wizard():
        sys.exit(0)

    try:
        listener = keyboard.GlobalHotKeys({'<ctrl>+<alt>+g': on_hotkey})
        listener.start()
    except Exception: 
        pass

    threading.Thread(target=listen_ipc, daemon=True).start()

    app = AppManager()
    app.root.mainloop()