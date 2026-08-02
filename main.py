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
    print("Warning: Pillow (PIL) is not installed. Images will not load.")

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
        try:
            os.remove(CONFIG_PATH)
            print("Config file automatically removed during uninstall.")
        except Exception:
            pass
    sys.exit(0)

def get_asset_path(filename):
    # Aggressively forces Python to look in the same directory as this script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.join(base_dir, filename)
    if not os.path.exists(target_path):
        # Fallback to current working directory just in case
        target_path = os.path.join(os.getcwd(), filename)
    return target_path

def set_window_icon(window):
    try: 
        window.wm_class("touch-grass-sim", "Touch Grass SIM")
    except Exception: 
        pass
    
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("touchgrass.sim.app.1.0")
        except Exception: 
            pass
            
    try:
        icon_path = get_asset_path("icon.png")
        if os.path.exists(icon_path):
            icon_img = ImageTk.PhotoImage(Image.open(icon_path))
            window.iconphoto(True, icon_img)
            window._icon_photo = icon_img
            
            if sys.platform == "win32":
                try:
                    window.iconbitmap(icon_path.replace(".png", ".ico"))
                except Exception:
                    pass
    except Exception as e:
        print(f"Failed to load icon.png: {e}")

def run_wizard():
    if os.path.exists(CONFIG_PATH):
        return True

    root = tk.Tk()
    root.title("Touch Grass SIM Setup")
    root.geometry("560x650")
    root.configure(bg="#2D3748")
    root.resizable(False, False)
    
    set_window_icon(root)

    canvas = tk.Canvas(root, width=560, height=180, bg="#1D2D44", highlightthickness=0)
    canvas.pack(fill="x")
    
    try:
        anime_path = get_asset_path("anime.png")
        pil_banner = Image.open(anime_path)
        pil_banner = ImageOps.fit(pil_banner, (560, 180), Image.Resampling.LANCZOS)
        banner_img = ImageTk.PhotoImage(pil_banner)
        canvas.create_image(0, 0, image=banner_img, anchor="nw")
        canvas.image = banner_img 
    except Exception as e:
        print(f"Failed to load anime.png: {e}")
        canvas.create_text(280, 90, text="TOUCH GRASS SIM (MISSING ANIME.PNG)", fill="#F4F1DE", font=("Helvetica", 16, "bold"))
    
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
        self.root.withdraw()
        self.overlay = None
        
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
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
            # DYNAMICALLY SPLIT ghibli.png INTO SKY AND GRASS
            img_path = get_asset_path("ghibli.png")
            raw_img = Image.open(img_path)
            
            # Scale image to exactly fit the screen
            scaled_img = ImageOps.fit(raw_img, (self.screen_width, self.screen_height), Image.Resampling.LANCZOS)
            
            # Define where the sky ends and grass begins (45% down the screen)
            split_y = int(self.screen_height * 0.45)
            
            # Crop the top half for the static sky
            sky_crop = scaled_img.crop((0, 0, self.screen_width, split_y))
            self.sky_img = ImageTk.PhotoImage(sky_crop)
            
            # Crop the bottom half for the moving grass
            # We add a little extra width buffer so the edges don't show when it sways
            buffer_width = self.screen_width + 100
            grass_scaled = ImageOps.fit(raw_img, (buffer_width, self.screen_height), Image.Resampling.LANCZOS)
            grass_crop = grass_scaled.crop((0, split_y, buffer_width, self.screen_height))
            self.grass_img = ImageTk.PhotoImage(grass_crop)
            
            def animate():
                if not self.overlay or not self.overlay.winfo_exists(): return
                canvas.delete("all")
                
                # Draw the static sky at the top left
                canvas.create_image(0, 0, image=self.sky_img, anchor="nw")
                
                # Draw the grass below the sky, swaying horizontally
                sway = math.sin(time.time() * 1.5) * 20
                canvas.create_image(-50 + sway, split_y, image=self.grass_img, anchor="nw")
                
                self.overlay.after(33, animate)
            
            animate()
            
        except Exception as e:
            print(f"Failed to load or slice ghibli.png: {e}")
            canvas.create_text(self.screen_width/2, self.screen_height/2, text="TIME TO TOUCH GRASS (ghibli.png missing)", fill="white", font=("Helvetica", 24, "bold"))

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
    
    # AUTOMATIC LAUNCH: Forces the break screen to open immediately so you know it works.
    EVENT_QUEUE.put("TRIGGER")

    app.root.mainloop()