import datetime
import os
import re
import time
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request

from buildmecar.camera_pi import Camera
from buildmecar.car import Car


def execute_command(cmd: str):
    r = os.popen(cmd)
    text = r.read()
    r.close()
    return text


video_devices = execute_command("ls /dev/video*")
print(f"Video devices detected: {video_devices}")
HAS_CAMERA_ON = bool(re.search(r"video0", video_devices, flags=re.I))
print(f"HAS_CAMERA_ON: {HAS_CAMERA_ON}")

DEFAULT_MOTOR_SPEED = 98
DEFAULT_MOTOR_PULSE = 1000

app = Flask(__name__)

# Global state for camera streaming
camera_streaming_enabled = False
camera_instance = None


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
        global camera_streaming_enabled, camera_instance
        if not camera_streaming_enabled or camera_instance is None:
            return Response("Camera streaming is disabled", status=503)

        return Response(
            gen(camera_instance), mimetype="multipart/x-mixed-replace; boundary=frame"
        )

    @app.route("/toggle_camera", methods=["POST"])
    def toggle_camera():
        """Toggle camera streaming on/off."""
        global camera_streaming_enabled, camera_instance
        try:
            camera_streaming_enabled = not camera_streaming_enabled
            print(f"Camera streaming toggled to: {camera_streaming_enabled}")

            if camera_streaming_enabled:
                if camera_instance is None:
                    print("Creating new Camera instance...")
                    camera_instance = Camera()
                print("Starting camera streaming...")
                camera_instance.start_streaming()
                print("Camera streaming started successfully")
            else:
                if camera_instance is not None:
                    print("Stopping camera streaming...")
                    camera_instance.stop_streaming()
                    print("Camera streaming stopped")

            return jsonify({"streaming": camera_streaming_enabled})
        except Exception as e:
            print(f"Error toggling camera: {e}")
            import traceback

            traceback.print_exc()
            camera_streaming_enabled = False
            return jsonify({"streaming": False, "error": str(e)}), 500

    @app.route("/camera_status")
    def camera_status():
        """Get current camera streaming status."""
        global camera_streaming_enabled
        return jsonify({"streaming": camera_streaming_enabled, "has_camera": True})

else:

    @app.route("/toggle_camera", methods=["POST"])
    def toggle_camera():
        """Toggle camera - no-op when camera doesn't exist."""
        return jsonify({"streaming": False, "has_camera": False})

    @app.route("/camera_status")
    def camera_status():
        """Get current camera streaming status when no camera exists."""
        return jsonify({"streaming": False, "has_camera": False})


def take_picture():
    global camera_instance
    if not HAS_CAMERA_ON:
        return "Camera not available"

    home = Path.home()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{home}/picture_{timestamp}.jpg"

    if camera_instance is None:
        camera_instance = Camera()

    camera_instance.take_picture(filename)
    return f"Picture saved to {filename}"


def main(status):
    result = None
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
            car.stop()
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
            result = take_picture()

    print(status, result)
    return result


@app.route("/")
def index():
    """Video streaming home page."""
    print(f"Rendering index with has_camera={HAS_CAMERA_ON}")
    return render_template("index.jinja", has_camera=HAS_CAMERA_ON)


@app.route("/cmd", methods=["GET", "POST"])
def button():
    if request.method == "POST":
        data = request.form.to_dict()
        result = main(data["id"])
        return jsonify({
            "status": "ok",
            "message": result if result else "command executed",
        })
    return render_template("index.jinja", has_camera=HAS_CAMERA_ON)


if __name__ == "__main__":
    # Initialize rc.local if on Raspberry Pi
    if os.path.exists("/etc/rc.local"):
        os.system("/etc/rc.local")
        time.sleep(1)

    # Initialize global car instance
    car = Car()
    app.run(host="0.0.0.0", port=5002, threaded=True, debug=False)
