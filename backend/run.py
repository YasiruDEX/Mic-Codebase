#!/usr/bin/env python3
"""
Classroom Whisper Monitor - Backend Entry Point
================================================
Starts the Firebase tracker with deep learning vocal filter.
Run this with: python run.py
"""

import logging
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def setup_logging():
    """Configure rich terminal logging."""
    # Create formatter with colors and structure
    formatter = logging.Formatter(
        fmt='%(asctime)s │ %(levelname)-7s │ %(message)s',
        datefmt='%H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('firebase_admin').setLevel(logging.WARNING)


def main():
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("  🎓 Classroom Whisper Monitor - Backend")
    logger.info("  🧠 Deep Learning Vocal Filter (Silero VAD)")
    logger.info("=" * 60)
    logger.info("")

    try:
        from firebase_tracker import run_tracker
        run_tracker()
    except KeyboardInterrupt:
        logger.info("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
