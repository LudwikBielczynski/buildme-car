import os
import re
import time

from flask import Flask, Response, render_template, request

from buildmecar.camera_pi import Camera
from buildmecar.car import Car


def execute_command(cmd: str):
    r = os.popen(cmd)
    text = r.read()
    r.close()
    return text


video_devices = execute_command("ls /dev/video*")
HAS_CAMERA_ON = re.search(r"video0", video_devices, flags=re.I)

DEFAULT_MOTOR_SPEED = 98
DEFAULT_MOTOR_PULSE = 1000

app = Flask(__name__)


# Automatically detects whether the camera exists and switches modes
if HAS_CAMERA_ON:

    def gen(camera):
        """Video streaming generator function."""
        yield b"--frame\r\n"
        while True:
            frame = camera.get_frame()
            yield b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n--frame\r\n"

    @app.route("/video_feed")
    def video_feed():
        """Video streaming route. Put this in the src attribute of an img tag."""
        return Response(
            gen(Camera()), mimetype="multipart/x-mixed-replace; boundary=frame"
        )


def main(status):
    match status:
        case "ic_up":
            car.front()
        case "ic_left":
            car.left()
        case "ic_right":
            car.right()
        case "ic_down":
            car.rear()
        case "ic_stop":
            car.stop
        case "stop":
            car.stop()
        case "ic_leftUp":
            car.front_left()
        case "ic_rightUp":
            car.front_right()
        case "ic_leftDown":
            car.rear_left()
        case "ic_rightDown":
            car.rear_right()

    print(status)


@app.route("/")
def index():
    """Video streaming home page."""
    if HAS_CAMERA_ON:
        return render_template("index.html")
    else:
        return render_template("index2.html")


@app.route("/cmd", methods=["GET", "POST"])
def button():
    if request.method == "POST":
        data = request.form.to_dict()
        main(data["id"])
    return render_template("index.html")


if __name__ == "__main__":
    os.system("/etc/rc.local")
    time.sleep(1)
    car = Car()
    car.stop()

    app.run(host="0.0.0.0", port=5002, threaded=True, debug=False)
