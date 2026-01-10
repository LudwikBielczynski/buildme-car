import io
import time

import picamera

from buildmecar.base_camera import BaseCamera


class Camera(BaseCamera):
    @staticmethod
    def frames():
        with picamera.PiCamera() as camera:
            # let camera warm up
            camera.exposure_mode = "auto"
            camera.awb_mode = "auto"

            time.sleep(2)
            gain = camera.awb_gains
            camera.awb_mode = "off"
            camera.awb_gains = gain

            stream = io.BytesIO()
            for _ in camera.capture_continuous(stream, "jpeg", use_video_port=True):
                # return current frame
                stream.seek(0)
                yield stream.read()

                # reset stream for next frame
                stream.seek(0)
                stream.truncate()
