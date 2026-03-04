"""
ReSpeaker Mic Array - Audio Uploader Tracker
============================================
- Captures live mic audio from the system input device
- Reads DOA from the ReSpeaker Mic Array hardware (if connected)
- Uploads compressed audio segments to the storage server
- Publishes real-time DOA + hardware metadata to Firebase
- Embeds hardware metadata in uploads for server-side VAD processing
"""
import sys
import os
import time
import logging
from dotenv import load_dotenv
import sounddevice as sd

import firebase_admin
from firebase_admin import credentials, db

# Audio Recorder
from audio_recorder import AudioRecorder

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from parent directory .env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add Mic Array script to path (from parent dir)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'usb_4_mic_array'))

# Audio stream configuration
SAMPLE_RATE = 16000
CHUNK_SAMPLES = 512
CHANNELS = 1

# Status update interval in seconds
STATUS_INTERVAL = float(os.getenv("STATUS_INTERVAL", "0.5"))

# Audio recording configuration
STORAGE_SERVER_URL = os.getenv("STORAGE_SERVER_URL", "http://localhost:5050")
AUDIO_SEGMENT_SECONDS = int(os.getenv("AUDIO_SEGMENT_SECONDS", "1"))

# Firebase configuration
FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL")
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "firebase-adminsdk.json")


def initialize_firebase():
    """Initialize Firebase Admin SDK for publishing DOA."""
    if not FIREBASE_DATABASE_URL:
        logger.warning("⚠️  FIREBASE_DATABASE_URL not set. Real-time DOA updates disabled.")
        return None

    try:
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        creds_path = FIREBASE_CREDENTIALS
        if not os.path.isabs(creds_path):
            creds_path = os.path.join(project_root, creds_path)

        if not firebase_admin._apps:
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred, {
                'databaseURL': FIREBASE_DATABASE_URL
            })

        logger.info("✅ Firebase initialized for real-time DOA publishing.")
        return db.reference('mic_data')
    except Exception as e:
        logger.error(f"❌ Firebase init failed: {e}")
        return None

def initialize_mic():
    """Find and initialize the ReSpeaker Mic Array (optional - graceful fallback)"""
    try:
        from tuning import Tuning
        import usb.core
        import usb.util

        dev = usb.core.find(idVendor=0x2886, idProduct=0x0018)
        if not dev:
            logger.warning("⚠️  ReSpeaker Mic Array not found. Hardware DOA/VAD disabled.")
            logger.warning("   Audio capture and upload will continue with system mic.")
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
    """Main tracking loop for audio upload + real-time DOA publishing to Firebase."""

    logger.info("=" * 60)
    logger.info("  Classroom Whisper Monitor - Backend")
    logger.info("  Audio Uploader + Real-time DOA Publisher")
    logger.info("=" * 60)

    # Step 1: Initialize Firebase for DOA publishing
    mic_data_ref = initialize_firebase()

    # Step 2: Initialize hardware mic array (optional)
    mic = initialize_mic()

    latest_hw_state = {
        "doa": 0,
        "is_voice_hw": False
    }

    def metadata_provider():
        return {
            "doa": latest_hw_state["doa"],
            "is_voice_hw": latest_hw_state["is_voice_hw"]
        }

    # Step 3: Initialize audio recorder/uploader
    logger.info("")
    logger.info("🔴 Initializing Audio Recorder...")
    audio_recorder = AudioRecorder(
        storage_server_url=STORAGE_SERVER_URL,
        segment_seconds=AUDIO_SEGMENT_SECONDS,
        sample_rate=SAMPLE_RATE,
        metadata_provider=metadata_provider
    )
    audio_recorder.start()

    # Step 4: Start audio input stream
    logger.info("🎤 Starting microphone stream...")
    stream = None

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        blocksize=CHUNK_SAMPLES,
        dtype='float32',
        callback=lambda indata, frames, time_info, status: audio_recorder.on_audio_chunk(indata[:, 0])
    )
    stream.start()

    logger.info("")
    logger.info("🚀 Audio upload tracker + real-time DOA publisher started!")
    logger.info(f"   Status interval: {STATUS_INTERVAL}s")
    logger.info(f"   Chunk duration: {AUDIO_SEGMENT_SECONDS}s (real-time VAD)")
    logger.info(f"   Storage server: {STORAGE_SERVER_URL}")
    if mic_data_ref:
        logger.info(f"   Firebase DOA updates: ✅ enabled")
    logger.info("   Press Ctrl+C to stop.")
    logger.info("-" * 60)

    status_count = 0

    try:
        while True:
            # Read hardware DOA and VAD (if mic array is connected)
            if mic:
                try:
                    latest_hw_state["doa"] = mic.direction
                    latest_hw_state["is_voice_hw"] = bool(mic.is_voice())
                except Exception:
                    latest_hw_state["doa"] = 0
                    latest_hw_state["is_voice_hw"] = False
            else:
                latest_hw_state["doa"] = 0
                latest_hw_state["is_voice_hw"] = False

            # Publish real-time DOA + hardware VAD to Firebase
            if mic_data_ref:
                try:
                    payload = {
                        "doa": latest_hw_state["doa"],
                        "is_voice_hw": latest_hw_state["is_voice_hw"],
                        "timestamp": int(time.time() * 1000)
                    }
                    mic_data_ref.update(payload)
                except Exception as e:
                    logger.error(f"❌ Firebase DOA publish failed: {e}")

            # Terminal logging
            status_count += 1
            recorder_status = audio_recorder.get_status()
            hw_status = "HW:🗣️ " if latest_hw_state["is_voice_hw"] else "HW:🔇"

            logger.info(
                f"#{status_count:06d} | "
                f"DOA: {latest_hw_state['doa']:03d}° | "
                f"{hw_status} | "
                f"Uploaded: {recorder_status['uploaded']} | "
                f"Buffered: {recorder_status['buffer_seconds']:.2f}s"
            )

            time.sleep(STATUS_INTERVAL)

    except KeyboardInterrupt:
        logger.info("")
        logger.info("🛑 Stopping tracker...")

    finally:
        if stream is not None:
            stream.stop()
            stream.close()
        audio_recorder.stop()
        logger.info(f"📊 Total status loops: {status_count}")
        logger.info("👋 Backend shut down cleanly.")


if __name__ == "__main__":
    # Configure logging for direct execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    run_tracker()
