import os
import shutil
import sys

def install_mac():
    print("Installing Touch Grass SIM for macOS...")
    
    app_dir = os.path.expanduser("~/Applications")
    os.makedirs(app_dir, exist_ok=True)
    
    plist_path = os.path.expanduser("~/Library/LaunchAgents/com.touchgrass.sim.plist")
    os.makedirs(os.path.dirname(plist_path), exist_ok=True)
    
    plist_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.touchgrass.sim</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>""" + os.path.abspath("main.py") + """</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
"""
    
    with open(plist_path, "w") as f:
        f.write(plist_content)
        
    print("LaunchAgent registered at:", plist_path)
    print("Touch Grass SIM macOS installation complete.")

if __name__ == "__main__":
    install_mac()