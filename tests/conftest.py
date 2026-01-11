"""
Pytest configuration and fixtures for buildmecar tests.
"""

import sys
from unittest.mock import MagicMock

# Mock picamera module for non-Raspberry Pi environments
sys.modules["picamera"] = MagicMock()

# Mock buildhat module for testing environments without hardware
sys.modules["buildhat"] = MagicMock()
