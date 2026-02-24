#!/usr/bin/env python3
"""
Audio Storage Server — Entry Point
====================================
Starts the Flask API server for receiving and storing compressed audio.

Run with: python run.py
"""

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def setup_logging():
    """Configure terminal logging."""
    formatter = logging.Formatter(
        fmt='%(asctime)s │ %(levelname)-7s │ %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # Suppress noisy Flask/Werkzeug logs
    logging.getLogger('werkzeug').setLevel(logging.WARNING)


def main():
    setup_logging()

    try:
        from server import app, STORAGE_PORT
        app.run(host='0.0.0.0', port=STORAGE_PORT, debug=False)
    except KeyboardInterrupt:
        print("\n👋 Storage server stopped.")
        sys.exit(0)
    except Exception as e:
        logging.getLogger(__name__).error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
