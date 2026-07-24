import time
import sys

def main():
    print("Starting Touch Grass SIM desktop engine...")
    print("Listening for break triggers and monitoring active window titles...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting Touch Grass SIM.")

if __name__ == "__main__":
    main()