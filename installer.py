import os
import sys
import winreg

def install_windows():
    print("Installing Touch Grass SIM for Windows...")
    
    script_path = os.path.abspath("main.py")
    python_exe = sys.executable
    
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "TouchGrassSim", 0, winreg.REG_SZ, f'"{python_exe}" "{script_path}"')
        winreg.CloseKey(key)
        print("Successfully added Touch Grass SIM to Windows Startup registry.")
    except Exception as e:
        print(f"Failed to write to registry: {e}")

if __name__ == "__main__":
    install_windows()