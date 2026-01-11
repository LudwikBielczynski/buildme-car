import io
import time

try:
    import picamera
except ImportError:
    picamera = None

from buildmecar.base_camera import BaseCamera


class Camera(BaseCamera):
    def frames(self):
        with picamera.PiCamera(resolution=(320, 240), framerate=10) as camera:
            camera.exposure_mode = "auto"
            camera.awb_mode = "auto"
            time.sleep(2)
            gain = camera.awb_gains
            camera.awb_mode = "off"
            camera.awb_gains = gain

            stream = io.BytesIO()
            for _ in camera.capture_continuous(stream, "jpeg", use_video_port=True):
                with self._lock:
                    if not self._streaming:
                        break
                stream.seek(0)
                yield stream.read()
                stream.seek(0)
                stream.truncate()

    def take_picture(self, filename):
        was_streaming = self._streaming
        if was_streaming:
            self.stop_streaming()
        with picamera.PiCamera() as camera:
            camera.exposure_mode = "auto"
            camera.awb_mode = "auto"
            time.sleep(2)
            gain = camera.awb_gains
            camera.awb_mode = "off"
            camera.awb_gains = gain
            camera.capture(filename)
        if was_streaming:
            self.start_streaming()
