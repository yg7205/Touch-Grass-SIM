import platform
import subprocess
import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

def set_system_mute(mute=True):
    os_name = platform.system()
    try:
        if os_name == "Windows":
            cmd = "$obj = new-object -com wscript.shell; $obj.SendKeys([char]173)"
            subprocess.run(["powershell", "-Command", cmd], capture_output=True)
        elif os_name == "Darwin": 
            state = "true" if mute else "false"
            subprocess.run(["osascript", "-e", f"set volume output muted {state}"])
        elif os_name == "Linux":
            state = "1" if mute else "0"
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", state])
    except Exception as e:
        print(f"Failed to change system volume: {e}")

def start_wind_audio(wind_path):
    set_system_mute(True)
    if not PYGAME_AVAILABLE or not wind_path or not os.path.exists(wind_path):
        return
        
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(wind_path)
        pygame.mixer.music.play(-1) # Loop forever
    except Exception as e:
        print(f"Audio playback failed: {e}")

def stop_wind_audio():
    if PYGAME_AVAILABLE and pygame.mixer.get_init():
        pygame.mixer.music.stop()
    set_system_mute(False)