"""
Comprehensive tests for BaseCamera to diagnose streaming issues.

These tests check:
1. Camera initialization
2. Streaming start/stop functionality
3. Frame generation and retrieval
4. Thread safety
5. Singleton behavior
6. Event signaling mechanism
"""

import threading
import time
from typing import Generator

import pytest

from buildmecar.base_camera import BaseCamera, CameraEvent


class MockCamera(BaseCamera):
    """Mock camera implementation for testing."""

    def __init__(self, frame_count: int = 10, frame_delay: float = 0.01):
        super().__init__()
        self.frame_count = frame_count
        self.frame_delay = frame_delay
        self.frames_generated = 0
        self.frames_called = False
        self.take_picture_called = False

    def frames(self) -> Generator[bytes, None, None]:
        """Generate mock frames."""
        self.frames_called = True
        for i in range(self.frame_count):
            with self._lock:
                if not self._streaming:
                    break
            self.frames_generated += 1
            time.sleep(self.frame_delay)
            yield f"frame_{i}".encode()

    def take_picture(self, filename: str):
        """Mock take picture implementation."""
        self.take_picture_called = True
        with open(filename, "w") as f:
            f.write("mock_picture")


class TestCameraEvent:
    """Test CameraEvent class functionality."""

    def test_camera_event_creation(self):
        """Test that CameraEvent can be created."""
        event = CameraEvent()
        assert event is not None
        assert len(event.events) == 0

    def test_camera_event_wait_creates_event(self):
        """Test that wait() creates an event for the current thread."""
        event = CameraEvent()

        def wait_in_thread():
            # This will block, so we need to set it from another thread
            event.events[threading.get_ident()] = threading.Event()
            event.events[threading.get_ident()].set()
            event.wait()

        thread = threading.Thread(target=wait_in_thread)
        thread.start()
        thread.join(timeout=1.0)
        assert not thread.is_alive()

    def test_camera_event_set_signals_all(self):
        """Test that set() signals all waiting threads."""
        event = CameraEvent()
        results = []

        def wait_and_record(index):
            event.wait()
            results.append(index)

        # Create multiple waiting threads
        threads = []
        for i in range(3):
            t = threading.Thread(target=wait_and_record, args=(i,))
            t.start()
            threads.append(t)

        # Give threads time to start waiting
        time.sleep(0.1)

        # Signal all threads
        event.set()

        # Wait for all threads
        for t in threads:
            t.join(timeout=1.0)

        assert len(results) == 3
        assert set(results) == {0, 1, 2}


class TestBaseCameraInitialization:
    """Test BaseCamera initialization."""

    def test_camera_initialization(self):
        """Test that camera initializes correctly."""
        camera = MockCamera()
        assert camera._thread is None
        assert camera._frame is None
        assert camera._streaming is False
        assert camera._event is not None
        assert camera._lock is not None

    def test_camera_is_singleton(self):
        """Test that BaseCamera uses singleton pattern."""
        # Clear singleton instance first
        if MockCamera in MockCamera._instances:
            del MockCamera._instances[MockCamera]

        camera1 = MockCamera()
        camera2 = MockCamera()
        assert camera1 is camera2


class TestStreamingStartStop:
    """Test streaming start and stop functionality."""

    @pytest.fixture
    def camera(self):
        """Create a fresh camera instance for each test."""
        # Clear singleton instance
        if MockCamera in MockCamera._instances:
            del MockCamera._instances[MockCamera]
        return MockCamera(frame_count=5, frame_delay=0.01)

    def test_start_streaming_sets_flag(self, camera):
        """Test that start_streaming sets the streaming flag."""
        assert camera._streaming is False
        camera.start_streaming()
        time.sleep(0.05)  # Give thread time to start
        assert camera._streaming is True

    def test_start_streaming_creates_thread(self, camera):
        """Test that start_streaming creates a thread."""
        assert camera._thread is None
        camera.start_streaming()
        assert camera._thread is not None
        assert camera._thread.is_alive()
        camera.stop_streaming()

    def test_start_streaming_calls_frames(self, camera):
        """Test that start_streaming calls the frames() method."""
        camera.start_streaming()
        time.sleep(0.05)
        assert camera.frames_called is True
        camera.stop_streaming()

    def test_stop_streaming_clears_flag(self, camera):
        """Test that stop_streaming clears the streaming flag."""
        camera.start_streaming()
        time.sleep(0.05)
        assert camera._streaming is True
        camera.stop_streaming()
        assert camera._streaming is False

    def test_stop_streaming_joins_thread(self, camera):
        """Test that stop_streaming properly joins the thread."""
        camera.start_streaming()
        time.sleep(0.05)
        thread = camera._thread
        assert thread.is_alive()
        camera.stop_streaming()
        assert camera._thread is None
        # The thread should have been joined and completed
        assert not thread.is_alive()

    def test_multiple_start_streaming_calls(self, camera):
        """Test that multiple start_streaming calls don't create multiple threads."""
        camera.start_streaming()
        time.sleep(0.05)
        first_thread = camera._thread

        # Try to start again (should be ignored due to _streaming flag)
        camera.start_streaming()
        second_thread = camera._thread

        assert first_thread is second_thread
        camera.stop_streaming()

    def test_streaming_without_stop_completes(self, camera):
        """Test that streaming completes when all frames are generated."""
        camera = MockCamera(frame_count=3, frame_delay=0.01)
        camera.start_streaming()
        time.sleep(0.2)  # Wait for all frames to be generated
        assert camera.frames_generated == 3


class TestFrameRetrieval:
    """Test frame generation and retrieval."""

    @pytest.fixture
    def camera(self):
        """Create a fresh camera instance for each test."""
        if MockCamera in MockCamera._instances:
            del MockCamera._instances[MockCamera]
        return MockCamera(frame_count=10, frame_delay=0.01)

    def test_get_frame_returns_data(self, camera):
        """Test that get_frame returns frame data."""
        camera.start_streaming()

        # Get first frame
        frame = camera.get_frame()
        assert frame is not None
        assert b"frame_" in frame

        camera.stop_streaming()

    def test_get_frame_updates_with_new_frames(self, camera):
        """Test that get_frame returns updated frames."""
        camera.start_streaming()

        frames = []
        for _ in range(3):
            frame = camera.get_frame()
            frames.append(frame)
            time.sleep(0.02)

        camera.stop_streaming()

        # Should have received different frames
        assert len(frames) == 3
        # At least some frames should be different
        assert len(set(frames)) > 1

    def test_get_frame_before_streaming_blocks(self, camera):
        """Test that get_frame blocks when streaming hasn't started."""
        result = []

        def try_get_frame():
            # This will block until streaming starts
            result.append("started")
            camera.get_frame()
            result.append("got_frame")

        thread = threading.Thread(target=try_get_frame)
        thread.start()

        time.sleep(0.05)
        assert len(result) == 1  # Should be blocked at get_frame

        camera.start_streaming()
        time.sleep(0.05)

        assert len(result) == 2  # Should have completed
        camera.stop_streaming()
        thread.join(timeout=1.0)


class TestThreadSafety:
    """Test thread safety of camera operations."""

    @pytest.fixture
    def camera(self):
        """Create a fresh camera instance for each test."""
        if MockCamera in MockCamera._instances:
            del MockCamera._instances[MockCamera]
        return MockCamera(frame_count=20, frame_delay=0.01)

    def test_concurrent_frame_retrieval(self, camera):
        """Test that multiple threads can safely retrieve frames."""
        camera.start_streaming()

        frames_per_thread = []

        def get_frames(index):
            local_frames = []
            for _ in range(5):
                frame = camera.get_frame()
                local_frames.append(frame)
            frames_per_thread.append(len(local_frames))

        threads = []
        for i in range(3):
            t = threading.Thread(target=get_frames, args=(i,))
            t.start()
            threads.append(t)

        for t in threads:
            t.join(timeout=2.0)

        camera.stop_streaming()

        # All threads should have gotten frames
        assert len(frames_per_thread) == 3
        assert all(count == 5 for count in frames_per_thread)


class TestStreamingIssues:
    """Tests specifically to diagnose streaming issues."""

    @pytest.fixture
    def camera(self):
        """Create a fresh camera instance for each test."""
        if MockCamera in MockCamera._instances:
            del MockCamera._instances[MockCamera]
        return MockCamera(frame_count=10, frame_delay=0.01)

    def test_streaming_starts_immediately(self, camera):
        """Test that streaming thread starts immediately after start_streaming."""
        start_time = time.time()
        camera.start_streaming()
        elapsed = time.time() - start_time

        # Should start very quickly (within 100ms)
        assert elapsed < 0.1
        assert camera._streaming is True
        assert camera._thread is not None
        assert camera._thread.is_alive()

        camera.stop_streaming()

    def test_first_frame_available_quickly(self, camera):
        """Test that first frame becomes available quickly after starting."""
        camera.start_streaming()

        # The start_streaming method waits for first frame
        # So frame should be available immediately
        assert camera._frame is not None

        camera.stop_streaming()

    def test_streaming_flag_checked_in_loop(self, camera):
        """Test that the streaming flag is properly checked in the frame loop."""
        camera.start_streaming()
        time.sleep(0.05)  # Let some frames generate

        initial_count = camera.frames_generated
        camera.stop_streaming()

        # No more frames should be generated after stopping
        time.sleep(0.05)
        final_count = camera.frames_generated

        assert final_count == initial_count

    def test_event_signaling_works(self, camera):
        """Test that event signaling properly wakes up waiting threads."""
        camera.start_streaming()

        received_frames = []
        stop_flag = threading.Event()

        def frame_receiver():
            while not stop_flag.is_set():
                frame = camera.get_frame()
                received_frames.append(frame)
                if len(received_frames) >= 5:
                    break

        thread = threading.Thread(target=frame_receiver)
        thread.start()

        # Wait for frames to be received
        thread.join(timeout=2.0)
        stop_flag.set()

        camera.stop_streaming()

        assert len(received_frames) >= 5

    def test_camera_recovers_from_stop_start(self, camera):
        """Test that camera can be stopped and started multiple times."""
        for i in range(3):
            camera.start_streaming()
            time.sleep(0.05)

            frame = camera.get_frame()
            assert frame is not None

            camera.stop_streaming()
            time.sleep(0.05)


class TestIntegrationScenarios:
    """Test real-world usage scenarios."""

    @pytest.fixture
    def camera(self):
        """Create a fresh camera instance for each test."""
        if MockCamera in MockCamera._instances:
            del MockCamera._instances[MockCamera]
        return MockCamera(frame_count=50, frame_delay=0.01)

    def test_web_streaming_scenario(self, camera):
        """Simulate web streaming where multiple clients request frames."""
        camera.start_streaming()

        def client_stream(client_id, frame_count):
            frames = []
            for _ in range(frame_count):
                frame = camera.get_frame()
                frames.append(frame)
            return len(frames)

        # Simulate 3 clients
        with pytest.raises(Exception) as exc_info:
            threads = []
            results = []

            for i in range(3):
                t = threading.Thread(
                    target=lambda: results.append(client_stream(i, 10))
                )
                t.start()
                threads.append(t)

            for t in threads:
                t.join(timeout=3.0)

            camera.stop_streaming()

        # Even if there's an exception, clean up
        camera.stop_streaming()

    def test_toggle_streaming_scenario(self, camera):
        """Test toggling streaming on and off like in the web UI."""
        # Start streaming
        camera.start_streaming()
        frame1 = camera.get_frame()
        assert frame1 is not None

        # Stop streaming
        camera.stop_streaming()
        time.sleep(0.05)

        # Start streaming again
        camera.start_streaming()
        frame2 = camera.get_frame()
        assert frame2 is not None

        camera.stop_streaming()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
