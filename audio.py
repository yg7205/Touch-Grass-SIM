import platform
import subprocess
import os
import sys

# Suppress the Pygame startup console greeting
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

def get_resource_path(relative_path):
    """Resolve absolute path to resource for Dev, PyInstaller, and Linux deb."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    local_path = os.path.join(base_path, relative_path)
    if os.path.exists(local_path):
        return local_path
        
    linux_path = f"/usr/share/touch-grass-sim/assets/{relative_path}"
    if os.path.exists(linux_path):
        return linux_path
        
    return local_path

def set_system_mute(mute=True):
    os_name = platform.system()
    try:
        if os_name == "Windows":
            # PowerShell command to toggle mute via virtual keycode
            cmd = "$obj = new-object -com wscript.shell; $obj.SendKeys([char]173)"
            subprocess.run(["powershell", "-Command", cmd], capture_output=True)
        elif os_name == "Darwin": # macOS
            state = "true" if mute else "false"
            subprocess.run(["osascript", "-e", f"set volume output muted {state}"])
        elif os_name == "Linux":
            state = "1" if mute else "0"
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", state])
    except Exception as e:
        print(f"Failed to change system volume: {e}")

def start_wind_audio():
    set_system_mute(True)
    if not PYGAME_AVAILABLE:
        return
        
    pygame.mixer.init()
    wind_path = get_resource_path("wind.mp3")
    
    if os.path.exists(wind_path):
        pygame.mixer.music.load(wind_path)
        pygame.mixer.music.play(-1) # -1 plays infinitely
    else:
        print(f"Wind audio file not found at {wind_path}")

def stop_wind_audio():
    if PYGAME_AVAILABLE and pygame.mixer.get_init():
        pygame.mixer.music.stop()
    set_system_mute(False)