import threading
import time
from abc import ABC, ABCMeta, abstractmethod

try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident


class SingletonMeta(ABCMeta):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class CameraEvent:
    """An Event-like class that signals all active clients when a new frame is
    available.
    """

    def __init__(self):
        self.events: dict[int : threading.Event()] = {}
        self.lock = threading.Lock()

    def wait(self, timeout=None):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        with self.lock:
            if ident not in self.events:
                self.events[ident] = threading.Event()
            event = self.events[ident]
        result = event.wait(timeout=timeout)
        event.clear()
        return result

    def set(self):
        """Invoked by the camera thread when a new frame is available."""
        with self.lock:
            for event in self.events.values():
                event.set()

    def clear(self):
        """Invoked from each client's thread after a frame was processed."""
        self.events[get_ident()][0].clear()


class BaseCamera(ABC, metaclass=SingletonMeta):
    def __init__(self):
        self._thread = None
        self._frame = None
        self._event = CameraEvent()
        self._lock = threading.Lock()
        self._streaming = False

    def _thread_run(self):
        try:
            print("Camera thread starting...")
            for frame in self.frames():
                with self._lock:
                    if not self._streaming:
                        break
                    self._frame = frame
                self._event.set()
                time.sleep(0)
            print("Camera thread finished normally")
        except Exception as e:
            print(f"Camera thread error: {e}")
            import traceback

            traceback.print_exc()
            with self._lock:
                self._streaming = False

    def start_streaming(self):
        with self._lock:
            if not self._streaming:
                self._streaming = True
                self._thread = threading.Thread(target=self._thread_run)
                self._thread.daemon = True
                self._thread.start()
        # Wait outside the lock with timeout
        print("Waiting for first frame (10 second timeout)...")
        success = self._event.wait(timeout=10.0)
        if not success:
            print("WARNING: Timeout waiting for first frame")
            raise TimeoutError("Camera failed to produce first frame within 10 seconds")

    def stop_streaming(self):
        with self._lock:
            self._streaming = False
        if self._thread is not None:
            self._thread.join()
            self._thread = None

    def get_frame(self):
        self._event.wait()
        with self._lock:
            return self._frame

    @abstractmethod
    def frames(self):
        raise NotImplementedError

    @abstractmethod
    def take_picture(self, filename):
        raise NotImplementedError
