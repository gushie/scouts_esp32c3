from simple_esp import Robot, Servo, SmallDisplay, Input
from machine import Pin
import time

robot = None
display = None

def main():
    global robot, display
    display = SmallDisplay()
    # Servos on Pin 0 and 1
    robot = Robot(Servo(0), Servo(1), speed=1, calibrate=0, display=display) 
    inp = Input(9)
    choice = display.menu(['Bluetooth', 'Browser', 'None'], inp)
    display.fill(0)
    if choice == 0:
        setup_bluetooth()
    elif choice == 1:
        setup_http()
    display.small_text_center('Robot', 4)
    display.show()        
    inp.on_click = robot_program
    while True:
        time.sleep_ms(50)

def robot_program():
    robot.forward(duration=1.5)
    robot.left(duration=0.5)
    robot.right(duration=1)
    robot.backward(duration=1)
    
def go(command):
    print(command)
    if command=='L':
        robot.left(duration=None)
    elif command=='R':
        robot.right(duration=None)
    elif command=='F':
        robot.forward(duration=None)
    elif command=='B':
        robot.backward(duration=None)
    elif command=='S':
        robot.stop()

def setup_bluetooth():
    from simple_esp import Bluetooth
    bus = Bluetooth()
    bus.start_scan()
    bus.on_text = go

def setup_http():
    from simple_esp import Http, connect_wifi
    def on_request(cmd):
        go(cmd)
        return """
            <html><body>
            <a href="/F">Forward</a><p>
            <a href="/L">Left</a><p>
            <a href="/S">Stop</a><p>
            <a href="/R">Right</a><p>
            <a href="/B">Back</a><p>
            </body></html>
        """
    wlan = connect_wifi()
    if wlan:
        ip = wlan.ifconfig()[0]
        display.small_text_center(ip, 24)
        http = Http()
        http.start(on_request)
        
if __name__ == "__main__":
    main()