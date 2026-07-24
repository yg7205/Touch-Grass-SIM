import os
import sys

def install_linux():
    print("Installing Touch Grass SIM for Linux...")
    
    bin_dir = os.path.expanduser("~/.local/bin")
    os.makedirs(bin_dir, exist_ok=True)
    
    autostart_dir = os.path.expanduser("~/.config/autostart")
    os.makedirs(autostart_dir, exist_ok=True)
    
    desktop_entry = f"""[Desktop Entry]
Type=Application
Name=Touch Grass SIM
Exec=python3 {os.path.abspath("main.py")}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
    
    desktop_file_path = os.path.join(autostart_dir, "touch-grass-sim.desktop")
    with open(desktop_file_path, "w") as f:
        f.write(desktop_entry)
        
    print("Autostart entry created at:", desktop_file_path)
    print("Touch Grass SIM Linux installation complete.")

if __name__ == "__main__":
    install_linux()