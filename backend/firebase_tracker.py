"""
ReSpeaker Mic Array - Firebase Realtime Tracker (with Deep Learning Vocal Filter)
=================================================================================
- Connects to Firebase Realtime Database
- Runs Silero VAD deep learning model for voice activity detection
- Reads DOA from the Mic Array hardware
- Pushes live updates (including DL voice probability) to Firebase
- Verbose logging to terminal
"""
import sys
import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Deep Learning Vocal Filter
from vocal_filter import VocalFilter

# Audio Recorder
from audio_recorder import AudioRecorder

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from parent directory .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add Mic Array script to path (from parent dir)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'usb_4_mic_array'))

# Project root directory (parent of backend/)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Firebase Configuration - resolve relative paths against project root
_firebase_creds = os.getenv("FIREBASE_CREDENTIALS", "firebase-adminsdk.json")
if not os.path.isabs(_firebase_creds):
    FIREBASE_CREDENTIALS_PATH = os.path.join(PROJECT_ROOT, _firebase_creds)
else:
    FIREBASE_CREDENTIALS_PATH = _firebase_creds
FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL")

# Vocal filter confidence threshold
VOICE_THRESHOLD = float(os.getenv("VOICE_THRESHOLD", "0.5"))

# Update interval in seconds
UPDATE_INTERVAL = float(os.getenv("UPDATE_INTERVAL", "0.1"))

# Audio recording configuration
STORAGE_SERVER_URL = os.getenv("STORAGE_SERVER_URL", "http://localhost:5050")
AUDIO_SEGMENT_SECONDS = int(os.getenv("AUDIO_SEGMENT_SECONDS", "30"))


def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        logger.info(f"🔥 Initializing Firebase...")
        logger.info(f"   Credentials: {FIREBASE_CREDENTIALS_PATH}")
        logger.info(f"   Database URL: {FIREBASE_DATABASE_URL}")

        if not FIREBASE_DATABASE_URL:
            logger.error("❌ FIREBASE_DATABASE_URL not found in .env")
            sys.exit(1)

        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_DATABASE_URL
        })
        logger.info("✅ Firebase initialized successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Firebase: {e}")
        sys.exit(1)


def initialize_mic():
    """Find and initialize the ReSpeaker Mic Array (optional - graceful fallback)"""
    try:
        from tuning import Tuning
        import usb.core
        import usb.util

        dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
        if not dev:
            logger.warning("⚠️  ReSpeaker Mic Array not found. Hardware DOA/VAD disabled.")
            logger.warning("   Deep learning vocal filter will still work with system mic.")
            return None

        logger.info("✅ ReSpeaker Mic Array found!")
        return Tuning(dev)

    except ImportError as e:
        logger.warning(f"⚠️  USB libraries not available: {e}")
        logger.warning("   Running without hardware mic array.")
        return None
    except Exception as e:
        logger.warning(f"⚠️  Could not initialize mic array: {e}")
        return None


def run_tracker():
    """Main tracking loop with deep learning vocal filter."""

    logger.info("=" * 60)
    logger.info("  Classroom Whisper Monitor - Backend")
    logger.info("  Deep Learning Vocal Filter (Silero VAD)")
    logger.info("=" * 60)

    # Step 1: Initialize Firebase
    initialize_firebase()

    # Step 2: Initialize hardware mic array (optional)
    mic = initialize_mic()

    # Step 3: Initialize deep learning vocal filter
    logger.info("")
    logger.info("🧠 Initializing Deep Learning Vocal Filter...")
    vocal_filter = VocalFilter(threshold=VOICE_THRESHOLD)

    # Step 4: Initialize audio recorder
    logger.info("")
    logger.info("🔴 Initializing Audio Recorder...")
    audio_recorder = AudioRecorder(
        storage_server_url=STORAGE_SERVER_URL,
        segment_seconds=AUDIO_SEGMENT_SECONDS
    )
    vocal_filter.add_audio_observer(audio_recorder.on_audio_chunk)
    audio_recorder.start()

    # Start vocal filter AFTER registering observers
    vocal_filter.start()

    # Firebase reference
    mic_data_ref = db.reference('mic_data')

    logger.info("")
    logger.info("🚀 Real-time Firebase sync started!")
    logger.info(f"   Update interval: {UPDATE_INTERVAL}s")
    logger.info(f"   Voice threshold: {VOICE_THRESHOLD}")
    logger.info(f"   Audio segments: {AUDIO_SEGMENT_SECONDS}s")
    logger.info("   Press Ctrl+C to stop.")
    logger.info("-" * 60)

    update_count = 0

    try:
        while True:
            # Read hardware DOA and VAD (if mic array is connected)
            if mic:
                try:
                    current_doa = mic.direction
                    hardware_vad = bool(mic.is_voice())
                except Exception:
                    current_doa = 0
                    hardware_vad = False
            else:
                current_doa = 0
                hardware_vad = False

            # Read deep learning voice probability
            dl_probability = vocal_filter.voice_probability
            dl_is_voice = vocal_filter.is_voice

            # Build payload
            timestamp = int(time.time() * 1000)
            payload = {
                'doa': current_doa,
                'is_voice': dl_is_voice,           # DL-based detection (primary)
                'is_voice_hw': hardware_vad,        # Hardware VAD (secondary)
                'voice_probability': round(dl_probability, 4),
                'timestamp': timestamp
            }

            # Push to Firebase
            mic_data_ref.set(payload)

            # Terminal logging
            update_count += 1
            now = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            # Build status bar
            prob_bar = "█" * int(dl_probability * 20) + "░" * (20 - int(dl_probability * 20))
            dl_status = "🗣️  VOICE" if dl_is_voice else "🔇 silent"
            hw_status = "HW:🗣️ " if hardware_vad else "HW:🔇"

            logger.info(
                f"[{now}] #{update_count:06d} | "
                f"DOA: {current_doa:03d}° | "
                f"DL: [{prob_bar}] {dl_probability:.3f} {dl_status} | "
                f"{hw_status}"
            )

            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:
        logger.info("")
        logger.info("🛑 Stopping tracker...")

    finally:
        vocal_filter.stop()
        audio_recorder.stop()
        logger.info(f"📊 Total updates sent: {update_count}")
        logger.info("👋 Backend shut down cleanly.")


if __name__ == "__main__":
    # Configure logging for direct execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    run_tracker()
