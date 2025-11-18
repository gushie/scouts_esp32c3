from simple_esp import Robot, Servo, SmallDisplay
from machine import Pin
import time

def main():
    # Servos on Pin 0 and 1
    display = SmallDisplay()
    display.fill(0)
    display.small_text_center('Robot', 16)
    display.show()
    robot = Robot(Servo(0), Servo(1), speed=1, calibrate=0, display=display) 
    button = Pin(9)

    while True:
        if button.value() == 0: # Start moving when button is pressed
            robot.forward(duration=2.5)
            robot.left(duration=1.5)
            robot.forward(duration=2)
            robot.right(duration=3)
            robot.backward(duration=1)
        time.sleep_ms(50)

if __name__ == "__main__":
    main()