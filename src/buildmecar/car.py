import time
from typing import NamedTuple

from buildhat import Hat, PassiveMotor


class MotorDirections(NamedTuple):
    right_rear: float
    right_front: float
    left_rear: float
    left_front: float


DEFAULT_MOTOR_SPEED = 98
DEFAULT_MOTOR_PULSE = 1000


class Car:
    def __init__(self):
        try:
            self.hat = Hat()
            self._has_motors = True
            print("Hat found. Motors initialized.")

        except FileNotFoundError:
            print("Hat not found. Working in emulation mode.")
            self._has_motors = False

        if self._has_motors:
            # Needs change depending on the place where the motors are connected
            self.motor_right_rear = PassiveMotor("D")
            self.motor_right_front = PassiveMotor("A")
            self.motor_left_rear = PassiveMotor("C")
            self.motor_left_front = PassiveMotor("B")

            self.directions_correction = MotorDirections(
                right_rear=1,
                right_front=1,
                left_rear=-1,
                left_front=-1,
            )

    def set_speed(self, port: int, speed: int = DEFAULT_MOTOR_SPEED):
        port.start(int(speed))

    def _run_motor(self, directions: MotorDirections, speed: int, time_ms: int) -> None:
        if not self._has_motors:
            print(
                f"SIMULATE: Motor command - directions={directions}, speed={speed}, time={time_ms}ms"
            )
            return
        self.set_speed(
            self.motor_right_rear,
            self.directions_correction.right_rear * directions.right_rear * speed,
        )
        self.set_speed(
            self.motor_right_front,
            self.directions_correction.right_front * directions.right_front * speed,
        )
        self.set_speed(
            self.motor_left_rear,
            self.directions_correction.left_rear * directions.left_rear * speed,
        )
        self.set_speed(
            self.motor_left_front,
            self.directions_correction.left_front * directions.left_front * speed,
        )
        time.sleep(time_ms / DEFAULT_MOTOR_PULSE)

    def front(self, speed: int = DEFAULT_MOTOR_SPEED, time_ms: int = 0) -> None:
        directions = MotorDirections(1, 1, 1, 1)
        self._run_motor(directions, speed, time_ms)

    def rear(self, speed: int = DEFAULT_MOTOR_SPEED, time_ms: int = 0) -> None:
        directions = MotorDirections(-1, -1, -1, -1)
        self._run_motor(directions, speed, time_ms)

    def right(self, speed=DEFAULT_MOTOR_SPEED, time_ms=0):
        directions = MotorDirections(-1, 1, 1, -1)
        self._run_motor(directions, speed, time_ms)

    def left(self, speed: int = DEFAULT_MOTOR_SPEED, time_ms: int = 0) -> None:
        directions = MotorDirections(1, -1, -1, 1)
        self._run_motor(directions, speed, time_ms)

    def front_left(self, speed: int = DEFAULT_MOTOR_SPEED, time_ms: int = 0) -> None:
        directions = MotorDirections(1.0 / 2, 1, -1.0 / 2, -1)
        self._run_motor(directions, speed, time_ms)

    def front_right(self, speed: int = DEFAULT_MOTOR_SPEED, time_ms: int = 0) -> None:
        directions = MotorDirections(-1.0, 0, 0.0, 0)
        self._run_motor(directions, speed, time_ms)

    def rear_left(self, speed: int = DEFAULT_MOTOR_SPEED, time_ms: int = 0) -> None:
        directions = MotorDirections(1, 1.0 / 2, -1, -1.0 / 2)
        self._run_motor(directions, speed, time_ms)

    def rear_right(self, speed: int = DEFAULT_MOTOR_SPEED, time_ms: int = 0) -> None:
        directions = MotorDirections(-1, -1.0 / 2, 1, 1.0 / 2)
        self._run_motor(directions, speed, time_ms)

    def stop(self) -> None:
        self.motor_right_rear.stop()
        self.motor_right_front.stop()
        self.motor_left_rear.stop()
        self.motor_left_front.stop()
