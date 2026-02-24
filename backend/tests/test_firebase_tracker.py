import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock deep learning VocalFilter, AudioRecorder, and firebase_admin before importing tracker
sys.modules['vocal_filter'] = MagicMock()
sys.modules['audio_recorder'] = MagicMock()

import firebase_tracker

class TestFirebaseTracker(unittest.TestCase):
    
    @patch('firebase_tracker.firebase_admin')
    @patch('firebase_tracker.credentials')
    def test_initialize_firebase_success(self, mock_credentials, mock_firebase_admin):
        # Temporarily mock the URL
        firebase_tracker.FIREBASE_DATABASE_URL = "https://mock.firebaseio.com"
        
        firebase_tracker.initialize_firebase()
        
        mock_credentials.Certificate.assert_called_once_with(firebase_tracker.FIREBASE_CREDENTIALS_PATH)
        mock_firebase_admin.initialize_app.assert_called_once_with(
            mock_credentials.Certificate.return_value, 
            {'databaseURL': "https://mock.firebaseio.com"}
        )

    @patch('usb.core.find')
    def test_initialize_mic_not_found(self, mock_usb_find):
        mock_usb_find.return_value = None
        
        mic = firebase_tracker.initialize_mic()
        
        self.assertIsNone(mic)
        mock_usb_find.assert_called_once_with(idVendor=0x2886, idProduct=0x0018)

    @patch('firebase_tracker.time')
    @patch('firebase_tracker.db')
    @patch('firebase_tracker.initialize_firebase')
    @patch('firebase_tracker.initialize_mic')
    @patch('firebase_tracker.VocalFilter')
    def test_run_tracker_loop(self, mock_VocalFilter, mock_init_mic, mock_init_firebase, mock_db, mock_time):
        # We need the loop to break after one iteration
        # So when time.sleep is called, raise KeyboardInterrupt
        mock_time.sleep.side_effect = KeyboardInterrupt
        mock_time.time.return_value = 1234567.89
        
        # Mock VocalFilter instance
        mock_vf_instance = mock_VocalFilter.return_value
        mock_vf_instance.voice_probability = 0.95
        mock_vf_instance.is_voice = True
        
        # Mock hardware mic
        mock_mic = MagicMock()
        mock_mic.direction = 180
        mock_mic.is_voice.return_value = 1
        mock_init_mic.return_value = mock_mic
        
        # Mock Firebase ref
        mock_ref = MagicMock()
        mock_db.reference.return_value = mock_ref
        
        # Run the tracker
        firebase_tracker.run_tracker()
        
        # Assertions
        mock_init_firebase.assert_called_once()
        mock_init_mic.assert_called_once()
        mock_vf_instance.start.assert_called_once()
        
        # Check that it pushed data to Firebase exactly once (before KeyboardInterrupt)
        mock_db.reference.assert_called_once_with('mic_data')
        
        expected_payload = {
            'doa': 180,
            'is_voice': True,
            'is_voice_hw': True,
            'voice_probability': 0.95,
            'timestamp': 1234567890
        }
        mock_ref.set.assert_called_once_with(expected_payload)
        
        # Ensure it stopped the vocal filter
        mock_vf_instance.stop.assert_called_once()

if __name__ == '__main__':
    unittest.main()
