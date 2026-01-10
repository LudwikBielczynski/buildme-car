import time

from buildhat import Hat, PassiveMotor


def main():
    hat = Hat()
    print(hat.get())

    motor_direction = 1

    # Initializing Motor
    for motor_name in ["A", "B", "C", "D"]:
        _motor = PassiveMotor(motor_name)
        print(f"Started motor {motor_name}")

        for i in range(0, 100):
            _motor.start(i * motor_direction)
            time.sleep(0.1)

        # delay 1s
        time.sleep(1)

        # Stop motor
        _motor.stop()
        # delay 1s
        time.sleep(1)


if __name__ == "__main__":
    main()
