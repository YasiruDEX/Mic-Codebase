"""
ReSpeaker Mic Array DOA (Direction of Arrival) Tracker
Continuously outputs the angle of the detected sound source (0-359 degrees)
"""
import sys
sys.path.insert(0, 'usb_4_mic_array')

from tuning import Tuning
import usb.core
import usb.util
import time

def main():
    # Find the ReSpeaker Mic Array device
    dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
    
    if not dev:
        print("ReSpeaker Mic Array not found!")
        print("Make sure the device is connected and the libusb driver is installed.")
        return
    
    print("ReSpeaker Mic Array found!")
    print("Tracking DOA (Direction of Arrival)...")
    print("Press Ctrl+C to stop\n")
    
    mic_tuning = Tuning(dev)
    
    try:
        while True:
            angle = mic_tuning.direction
            print(f"Sound Angle: {angle}°", end='\r')
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\nStopped tracking.")

if __name__ == "__main__":
    main()
