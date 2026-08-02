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
# When you uninstall the thing across all softwares it automatically removes that file
if "--uninstall" in sys.argv:
    if os.path.exists(CONFIG_PATH):
        os.remove(CONFIG_PATH)
    sys.exit(0)

def get_asset_path(filename):
    # Absolute path resolution pointing directly to the main directory
    return os.path.abspath(os.path.join(os.path.dirname(__file__), filename))

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
            
    # 3. FORCE APPLY ICON
    try:
        icon_path = get_asset_path("icon.png")
        icon_img = ImageTk.PhotoImage(Image.open(icon_path))
        window.iconphoto(True, icon_img)
        window._icon_photo = icon_img
        
        # Windows fallback for older Tkinter versions
        if sys.platform == "win32":
            window.iconbitmap(icon_path.replace(".png", ".ico"))
    except Exception as e:
        print(f"Icon error: {e}")

def run_wizard():
    # If the config exists, we already did this. Skip it!
    if os.path.exists(CONFIG_PATH):
        return True

    root = tk.Tk()
    root.title("Touch Grass SIM Setup")
    root.geometry("560x650")
    root.configure(bg="#2D3748")
    root.resizable(False, False)
    
    set_window_icon(root)

    # BANNER - Strictly uses anime.png from the main directory
    canvas = tk.Canvas(root, width=560, height=180, bg="#1D2D44", highlightthickness=0)
    canvas.pack(fill="x")
    
    try:
        pil_banner = Image.open(get_asset_path("anime.png"))
        pil_banner = ImageOps.fit(pil_banner, (560, 180), Image.Resampling.LANCZOS)
        banner_img = ImageTk.PhotoImage(pil_banner)
        canvas.create_image(0, 0, image=banner_img, anchor="nw")
        canvas.image = banner_img 
    except Exception:
        canvas.create_text(280, 90, text="TOUCH GRASS SIM", fill="#F4F1DE", font=("Helvetica", 22, "bold"))
    
    # EULA TEXT BOX
    eula_frame = tk.Frame(root, bg="#2D3748")
    eula_frame.pack(fill="both", expand=True, padx=20, pady=15)
    
    eula_label = tk.Label(eula_frame, text="End User License Agreement", bg="#2D3748", fg="white", font=("Helvetica", 12, "bold"))
    eula_label.pack(anchor="w", pady=(0, 5))

    text_scroll = tk.Scrollbar(eula_frame)
    text_scroll.pack(side="right", fill="y")
    
    eula_text = tk.Text(eula_frame, wrap="word", yscrollcommand=text_scroll.set, bg="#1D2D44", fg="#E2E8F0", height=10, padx=10, pady=10)
    eula_text.insert("1.0", "Welcome to Touch Grass SIM.\n\n1. By installing this software, you agree to take mandatory mindfulness breaks to prevent burnout.\n2. When the break screen appears, you will pause your work.\n3. This software runs in the background and respects your privacy.\n\nPlease accept to continue installation.")
    eula_text.config(state="disabled")
    eula_text.pack(side="left", fill="both", expand=True)
    text_scroll.config(command=eula_text.yview)

    # CHECKBOX & BUTTONS
    bottom_frame = tk.Frame(root, bg="#2D3748")
    bottom_frame.pack(side="bottom", fill="x", padx=20, pady=20)
    
    agree_var = tk.IntVar()
    
    def on_check():
        if agree_var.get() == 1:
            accept_btn.config(state="normal", bg="#48BB78")
        else:
            accept_btn.config(state="disabled", bg="#374151")

    check = tk.Checkbutton(bottom_frame, text="I have read and agree to the terms", variable=agree_var, command=on_check, bg="#2D3748", fg="white", selectcolor="#1D2D44", activebackground="#2D3748", activeforeground="white", highlightthickness=0)
    check.pack(pady=(0, 15))

    btn_container = tk.Frame(bottom_frame, bg="#2D3748")
    btn_container.pack()

    def on_accept():
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump({"setup_complete": True}, f)
        root.destroy()

    def on_cancel():
        sys.exit(0)

    cancel_btn = tk.Button(btn_container, text="Cancel", command=on_cancel, bg="#EF4444", fg="white", width=15, pady=5)
    cancel_btn.pack(side="left", padx=10)

    accept_btn = tk.Button(btn_container, text="Accept & Continue", state="disabled", command=on_accept, bg="#374151", fg="white", width=15, pady=5)
    accept_btn.pack(side="left", padx=10)
    
    root.mainloop()
    return os.path.exists(CONFIG_PATH)

class AppManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() # Hide the background window
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