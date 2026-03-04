"""
Firebase publisher for server-side mic updates.
"""

import os
import logging

import firebase_admin
from firebase_admin import credentials, db

logger = logging.getLogger(__name__)


class FirebasePublisher:
    """Thin wrapper around Firebase Realtime Database writes."""

    def __init__(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        firebase_creds = os.getenv("FIREBASE_CREDENTIALS", "firebase-adminsdk.json")
        if not os.path.isabs(firebase_creds):
            self._credentials_path = os.path.join(project_root, firebase_creds)
        else:
            self._credentials_path = firebase_creds

        self._database_url = os.getenv("FIREBASE_DATABASE_URL")
        self._enabled = bool(self._database_url)

        if self._enabled:
            self._initialize()
        else:
            logger.warning("⚠️  FIREBASE_DATABASE_URL not set. Firebase publish disabled.")

    @property
    def enabled(self):
        return self._enabled

    def _initialize(self):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(self._credentials_path)
                firebase_admin.initialize_app(cred, {
                    'databaseURL': self._database_url
                })
            self._ref = db.reference('mic_data')
            logger.info("✅ Firebase publisher initialized.")
        except Exception as e:
            self._enabled = False
            logger.error(f"❌ Failed to initialize Firebase publisher: {e}")

    def publish(self, payload: dict):
        if not self._enabled:
            return False

        try:
            # Use update() to merge VAD fields without overwriting DOA/timestamp
            self._ref.update(payload)
            return True
        except Exception as e:
            logger.error(f"❌ Failed to publish to Firebase: {e}")
            return False
