# message.py — Send message over bluetooth

from simple_esp import Input, SmallDisplay, Bluetooth, Registry
from machine import Pin
import time

# MENU: Write your phrases here 👇
PHRASES = [
    "Hello",
    "Yes",
    "No",
    "Bye",
    "Maybe",
    "Thank you",
    "Great!",
    "Where are you?",
    "On my way",
    "I'm ready",
]

bus = Bluetooth()    # discovery-based; no MACs needed
display = SmallDisplay()
led = Pin(8, Pin.OUT)
inp = Input(9)

# BUTTON: double press = send preset message (index-based)
def send_text(current):
    display.notify("Sending...", ms=300)
    # Get the username we may have saved in message.py
    user = Registry().get("msg.username", "Anon")
    # So this works with 'message.py', user + |*|M| just says this is from user to all (*) and is a message (M).
    message = user + "|*|M|" + PHRASES[current]
    bus.send_text(message)     # <— send preset index to other devices
    led.value(1)
    time.sleep_ms(500)
    led.value(0)

def on_receive_text(text):
    """Handle incoming text-based message."""
    # Show up to 14 chars to fit the display width
    parts = (text or "").split("|", 3)
    if parts[1] == "*" and parts[2] == "M":
        msg = "RX: " + (parts[3] or "")[:14]
        led.value(1)
        display.notify(msg)
        led.value(0)
        display.refresh_menu()

def main():
    # Button + BLE setup
    bus.on_text = on_receive_text
    bus.start_scan()
    bus.presence()  # optional "hello" burst

    # Brief instructions on screen
    display.fill(0)
    display.small_text("Scout Messenger", 0, 0)
    display.small_text("Click: next",     0, 8)
    display.small_text("Dbl Clk: send",   0, 16)
    display.show()
    time.sleep_ms(2500)

    # Start in menu mode
    while True:
        current = display.menu(PHRASES, inp)
        send_text(current)

if __name__ == "__main__":
    main()