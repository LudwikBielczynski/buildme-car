import threading
import time
from abc import ABC, abstractmethod

try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident


class SingletonMeta(type):
    _instance = None
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class CameraEvent:
    """An Event-like class that signals all active clients when a new frame is
    available.
    """

    def __init__(self):
        self.events: dict[int : threading.Event()] = {}
        self.lock = threading.Lock()

    def wait(self):
        """Invoked from each client's thread to wait for the next frame."""
        ident = get_ident()
        with self.lock:
            if ident not in self.events:
                self.events[ident] = threading.Event()
            event = self.events[ident]
        event.wait()
        event.clear()

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
        for frame in self.frames():
            with self._lock:
                if not self._streaming:
                    break
                self._frame = frame
            self._event.set()
            time.sleep(0)

    def start_streaming(self):
        with self._lock:
            if not self._streaming:
                self._streaming = True
                self._thread = threading.Thread(target=self._thread_run)
                self._thread.daemon = True
                self._thread.start()
                self._event.wait()

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
