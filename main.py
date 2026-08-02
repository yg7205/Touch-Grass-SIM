#!/usr/bin/env python3
import os
import sys
import time
import math
import json
import socket
import threading
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

# --- UNINSTALLER: ORPHAN FILE CLEANUP ---
if "--uninstall" in sys.argv:
    if os.path.exists(CONFIG_PATH):
        os.remove(CONFIG_PATH)
    sys.exit(0)

def get_asset_path(filename):
    return os.path.join(os.path.dirname(__file__), "assets", filename)

def run_wizard():
    if os.path.exists(CONFIG_PATH):
        return True

    root = tk.Tk()
    root.title("Touch Grass SIM Setup")
    root.geometry("540x600")
    root.configure(bg="#2D3748")

    canvas = tk.Canvas(root, width=540, height=180, bg="#1D2D44", highlightthickness=0)
    canvas.pack(fill="x")
    
    # Wizard banner using anime.png
    try:
        pil_banner = Image.open(get_asset_path("anime.png"))
        pil_banner = ImageOps.fit(pil_banner, (540, 180), Image.Resampling.LANCZOS)
        banner_img = ImageTk.PhotoImage(pil_banner)
        canvas.create_image(0, 0, image=banner_img, anchor="nw")
        canvas.image = banner_img 
    except Exception:
        canvas.create_text(270, 90, text="TOUCH GRASS SIM", fill="#F4F1DE", font=("Helvetica", 22, "bold"))
    
    # Fix: Buttons are explicitly colored so they are never blank
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

def trigger_break():
    # Fix: Cut off external sound and play wind.mp3
    try:
        audio.mute_system_audio()
        audio.start_wind_audio(get_asset_path("wind.mp3"))
    except Exception:
        pass

    overlay = tk.Tk()
    overlay.attributes("-fullscreen", True)
    overlay.attributes("-topmost", True)
    
    canvas = tk.Canvas(overlay, bg="#0B132B", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    try:
        sky_img = ImageTk.PhotoImage(Image.open(get_asset_path("sky.png")))
        grass_img = ImageTk.PhotoImage(Image.open(get_asset_path("ghibli.png")))
        
        def animate():
            if not overlay.winfo_exists():
                return
            canvas.delete("all")
            canvas.create_image(0, 0, image=sky_img, anchor="nw")
            # Fix: Natural grass swaying using smooth math.sin
            sway = math.sin(time.time() * 1.5) * 20
            canvas.create_image(-50 + sway, 500, image=grass_img, anchor="nw")
            overlay.after(33, animate)
        animate()
    except Exception:
        pass

    def on_close():
        try:
            audio.stop_wind_audio()
            audio.unmute_system_audio()
        except Exception:
            pass
        overlay.destroy()
        
    tk.Button(overlay, text="Return to Work", command=on_close, bg="#48BB78", fg="black", font=("Helvetica", 14, "bold")).place(relx=0.5, rely=0.5, anchor="center")
    overlay.mainloop()

def on_hotkey():
    trigger_break()

def listen_ipc():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind(("127.0.0.1", IPC_PORT))
        server.listen(1)
        while True:
            server.accept()
            trigger_break()
    except Exception:
        pass

if __name__ == "__main__":
    # 1. WIZARD COMES FIRST 
    if not run_wizard():
        sys.exit(0)

    # 2. HOTKEY TRIGGER (Ctrl + Alt + G)
    try:
        listener = keyboard.GlobalHotKeys({'<ctrl>+<alt>+g': on_hotkey})
        listener.start()
    except Exception:
        pass

    # 3. BACKGROUND SERVER
    listen_ipc()