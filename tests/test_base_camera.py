"""
Tests for BaseCamera functionality.

Tests cover:
- Camera initialization and singleton behavior
- Starting and stopping streaming
- Frame generation and retrieval
- Thread safety for concurrent access
"""

import threading
import time
from typing import Generator

import pytest

from buildmecar.base_camera import BaseCamera


class MockCamera(BaseCamera):
    """Simple mock camera for testing."""

    def __init__(self, frame_count: int = 10, frame_delay: float = 0.01):
        super().__init__()
        self.frame_count = frame_count
        self.frame_delay = frame_delay
        self.frames_generated = 0

    def frames(self) -> Generator[bytes, None, None]:
        """Generate mock frames."""
        for i in range(self.frame_count):
            with self._lock:
                if not self._streaming:
                    break
            self.frames_generated += 1
            time.sleep(self.frame_delay)
            yield f"frame_{i}".encode()

    def take_picture(self, filename: str):
        """Mock take picture implementation."""
        with open(filename, "w") as f:
            f.write("mock_picture")


@pytest.fixture
def camera():
    """Create a fresh camera instance for each test."""
    # Clear singleton instance
    if MockCamera in MockCamera._instances:
        del MockCamera._instances[MockCamera]
    cam = MockCamera(frame_count=10, frame_delay=0.01)
    yield cam
    # Cleanup
    if cam._streaming:
        cam.stop_streaming()


class TestCameraBasics:
    """Test basic camera functionality."""

    def test_camera_initializes_correctly(self, camera):
        """Camera should initialize with streaming off."""
        assert not camera._streaming
        assert camera._thread is None
        assert camera._frame is None

    def test_camera_is_singleton(self):
        """Same camera instance should be returned."""
        if MockCamera in MockCamera._instances:
            del MockCamera._instances[MockCamera]

        cam1 = MockCamera()
        cam2 = MockCamera()
        assert cam1 is cam2

        if cam1._streaming:
            cam1.stop_streaming()

    @pytest.mark.parametrize(
        "frame_count,delay",
        [
            (5, 0.01),
            (10, 0.005),
            (3, 0.02),
        ],
    )
    def test_camera_generates_frames(self, frame_count, delay):
        """Camera should generate the specified number of frames."""
        if MockCamera in MockCamera._instances:
            del MockCamera._instances[MockCamera]

        camera = MockCamera(frame_count=frame_count, frame_delay=delay)
        camera.start_streaming()

        # Wait for all frames to be generated
        time.sleep((frame_count + 2) * delay)

        camera.stop_streaming()
        assert camera.frames_generated <= frame_count


class TestStreaming:
    """Test streaming start and stop."""

    def test_start_streaming_enables_streaming(self, camera):
        """Starting streaming should set the flag and create thread."""
        camera.start_streaming()

        assert camera._streaming
        assert camera._thread is not None
        assert camera._frame is not None  # First frame should be available

        camera.stop_streaming()

    def test_stop_streaming_disables_streaming(self, camera):
        """Stopping streaming should clear flag and clean up thread."""
        camera.start_streaming()
        camera.stop_streaming()

        assert not camera._streaming
        assert camera._thread is None

    def test_restart_streaming(self, camera):
        """Camera should handle stop/start cycles."""
        # First cycle
        camera.start_streaming()
        frame1 = camera.get_frame()
        camera.stop_streaming()

        # Second cycle
        camera.start_streaming()
        frame2 = camera.get_frame()
        camera.stop_streaming()

        assert frame1 is not None
        assert frame2 is not None

    def test_stop_prevents_new_frames(self, camera):
        """Stopping should prevent new frames from being generated."""
        camera.start_streaming()
        time.sleep(0.05)

        initial_count = camera.frames_generated
        camera.stop_streaming()
        time.sleep(0.05)

        assert camera.frames_generated == initial_count


class TestFrameRetrieval:
    """Test getting frames from the camera."""

    def test_get_frame_returns_data(self, camera):
        """get_frame should return frame data."""
        camera.start_streaming()

        frame = camera.get_frame()
        assert frame is not None
        assert b"frame_" in frame

        camera.stop_streaming()

    def test_get_frame_returns_different_frames(self, camera):
        """get_frame should return updated frames over time."""
        camera.start_streaming()

        frames = []
        for _ in range(3):
            frame = camera.get_frame()
            frames.append(frame)
            time.sleep(0.02)

        camera.stop_streaming()

        # At least some frames should differ
        assert len(set(frames)) >= 2

    def test_concurrent_frame_access(self, camera):
        """Multiple threads should safely access frames."""
        camera.start_streaming()

        received = []

        def get_frames():
            for _ in range(5):
                frame = camera.get_frame()
                received.append(frame)

        threads = [threading.Thread(target=get_frames) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=2.0)

        camera.stop_streaming()

        # All threads should have received frames
        assert len(received) == 15  # 3 threads × 5 frames


class TestTakePicture:
    """Test taking pictures."""

    def test_take_picture_creates_file(self, camera, tmp_path):
        """take_picture should create a file."""
        filename = str(tmp_path / "test.jpg")
        camera.take_picture(filename)

        assert (tmp_path / "test.jpg").exists()
        content = (tmp_path / "test.jpg").read_text()
        assert content == "mock_picture"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
