import os
import re
import time

from buildhat import PassiveMotor
from flask import Flask, Response, render_template, request

from buildmecar.camera_pi import Camera


def execute_command(cmd):
    r = os.popen(cmd)
    text = r.read()
    r.close()
    return text


video_devices = execute_command("ls /dev/video*")
detect_flag = re.search(r"video0", video_devices, flags=re.I)

app = Flask(__name__)


class Car(object):
    def __init__(self):
        # device need connected

        self.motor_right_rear = PassiveMotor("A")
        self.motor_right_front = PassiveMotor("B")
        self.motor_left_rear = PassiveMotor("C")
        self.motor_left_front = PassiveMotor("D")

    def set_speed(self, port: int, speed: int = 100):
        port.start(int(speed))

    #   The following functions need to match the Raspberry Pi Build HAT port with the LEGO motor,
    #   otherwise it will not work properly

    def front(self, speed=100, time_ms=0):
        self.set_speed(self.motor_right_rear, speed)
        self.set_speed(self.motor_right_front, speed)
        self.set_speed(self.motor_left_rear, -speed)
        self.set_speed(self.motor_left_front, -speed)
        time.sleep(time_ms / 1000)

    def rear(self, speed=100, time_ms=0):
        self.set_speed(self.motor_right_rear, -speed)
        self.set_speed(self.motor_right_front, -speed)
        self.set_speed(self.motor_left_rear, speed)
        self.set_speed(self.motor_left_front, speed)
        time.sleep(time_ms / 1000)

    def right(self, speed=100, time_ms=0):
        self.set_speed(self.motor_right_rear, -speed)
        self.set_speed(self.motor_right_front, speed)
        self.set_speed(self.motor_left_rear, -speed)
        self.set_speed(self.motor_left_front, speed)
        time.sleep(time_ms / 1000)

    def left(self, speed=100, time_ms=0):
        self.set_speed(self.motor_right_rear, speed)
        self.set_speed(self.motor_right_front, -speed)
        self.set_speed(self.motor_left_rear, speed)
        self.set_speed(self.motor_left_front, -speed)
        time.sleep(time_ms / 1000)

    def front_left(self, speed=100, time_ms=0):
        self.set_speed(self.motor_right_rear, speed)
        self.set_speed(self.motor_right_front, speed)
        self.set_speed(self.motor_left_rear, -speed / 5)
        self.set_speed(self.motor_left_front, -speed / 5)
        time.sleep(time_ms / 1000)

    def front_right(self, speed=100, time_ms=0):
        self.set_speed(self.motor_right_rear, speed / 5)
        self.set_speed(self.motor_right_front, speed / 5)
        self.set_speed(self.motor_left_rear, -speed)
        self.set_speed(self.motor_left_front, -speed)
        time.sleep(time_ms / 1000)

    def rear_left(self, speed=100, time_ms=0):
        self.front_left(-speed, time_ms)

    def rear_right(self, speed=100, time_ms=0):
        self.front_right(-speed, time_ms)

    def stop(self):
        self.motor_right_rear.stop()
        self.motor_right_front.stop()
        self.motor_left_rear.stop()
        self.motor_left_front.stop()


def main(status):
    if status == "ic_up":
        car.front()
    elif status == "ic_left":
        car.left()
    elif status == "ic_right":
        car.right()
    elif status == "ic_down":
        car.rear()
    elif status == "ic_stop":
        car.stop()
    elif status == "stop":
        car.stop()
    elif status == "ic_leftUp":
        car.front_left()
    elif status == "ic_rightUp":
        car.front_right()
    elif status == "ic_leftDown":
        car.rear_left()
    elif status == "ic_rightDown":
        car.rear_right()
    print(status)


@app.route("/")
def index():
    """Video streaming home page."""
    if detect_flag:
        return render_template("index.html")
    else:
        return render_template("index2.html")


@app.route("/cmd", methods=["GET", "POST"])
def button():
    if request.method == "POST":
        data = request.form.to_dict()
        main(data["id"])
    return render_template("index.html")


# Automatically detects whether the camera exists and switches modes
if detect_flag:

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


if __name__ == "__main__":
    os.system("/etc/rc.local")
    time.sleep(1)
    car = Car()
    car.stop()

    app.run(host="0.0.0.0", port=5002, threaded=True, debug=False)
