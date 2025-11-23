# message.py — Send message over bluetooth

from simple_esp import SmallDisplay, Bluetooth, Input

# MENU: Write your phrases here 👇
PHRASES = [
    "Stop",
    "Forward",
    "Left",
    "Right",
    "Back"
]

def send_text(bus, current):
    bus.send_text(PHRASES[current][:1])     

def main():
    bus = Bluetooth() 
    display = SmallDisplay()
    inp = Input(9)
    while True:
        current = display.menu(PHRASES, inp)
        send_text(bus, current)

if __name__ == "__main__":
    main()
