import datetime
import os
import re
import time
from pathlib import Path

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


def take_picture():
    home = Path.home()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{home}/picture_{timestamp}.jpg"
    Camera.take_picture(filename)
    return f"Picture saved to {filename}"


def main(status):
    match status:
        case "ic-up":
            car.front()
        case "ic-left":
            car.left()
        case "ic-right":
            car.right()
        case "ic-down":
            car.rear()
        case "ic-stop":
            car.stop
        case "stop":
            car.stop()
        case "ic-left-up":
            car.front_left()
        case "ic-right-up":
            car.front_right()
        case "ic-left-down":
            car.rear_left()
        case "ic-right-down":
            car.rear_right()
        case "take-picture":
            status = take_picture()

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
