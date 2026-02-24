"""
ReSpeaker Mic Array - Firebase Realtime Tracker
===============================================
- Connects to Firebase Realtime Database
- Continuously reads DOA and Voice Activity Detection (VAD) from the Mic Array
- Pushes live updates to Firebase for the React frontend to consume
"""
import sys
import os
import time
from dotenv import load_dotenv

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Load environment variables
load_dotenv()

# Add Mic Array script to path
sys.path.insert(0, 'usb_4_mic_array')

from tuning import Tuning
import usb.core
import usb.util

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS", "firebase-adminsdk.json")
FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL")

if not FIREBASE_DATABASE_URL:
    print("Error: FIREBASE_DATABASE_URL not found in .env")
    sys.exit(1)

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        print(f"Initializing Firebase with credentials from: {FIREBASE_CREDENTIALS_PATH}")
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_DATABASE_URL
        })
        print("Firebase initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")
        sys.exit(1)

def initialize_mic():
    """Find and initialize the ReSpeaker Mic Array"""
    dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
    if not dev:
        print("ReSpeaker Mic Array not found! Make sure it is connected.")
        sys.exit(1)
    
    print("ReSpeaker Mic Array found! Getting tuning instance...")
    return Tuning(dev)

def main():
    initialize_firebase()
    mic = initialize_mic()
    
    # Reference to the Firebase Realtime Database node
    mic_data_ref = db.reference('mic_data')
    
    print("\nStarting Real-time Firebase Sync...")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            # Read from mic
            current_doa = mic.direction
            # mic.is_voice() returns an integer (0 or 1), let's cast to bool
            current_vad = bool(mic.is_voice())
            
            # Additional logic to determine if it might be a whisper
            # For this simple setup, if we have VAD active, we just register it.
            # In a more advanced setup, we might look at volume/energy levels.
            
            payload = {
                'doa': current_doa,
                'is_voice': current_vad,
                'timestamp': int(time.time() * 1000) # JS compatible timestamp
            }
            
            # Push to Firebase
            mic_data_ref.set(payload)
            
            status = "🗣 Voice Detected" if current_vad else "🔇 Silence"
            print(f"Synced -> DOA: {current_doa:03d}° | Status: {status}", end='\r')
            
            # Update interval (e.g., every 100ms)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n\nStopped Firebase Sync.")

if __name__ == "__main__":
    main()
