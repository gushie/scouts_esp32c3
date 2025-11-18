# message.py — Send message over bluetooth

from simple_esp import Input, SmallDisplay, Bluetooth, Keyboard
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

MODE_MENU = 0
MODE_KEYBOARD = 1

current = 0          # index into PHRASES
mode = MODE_MENU

bus = Bluetooth()    # discovery-based; no MACs needed
display = SmallDisplay()
led = Pin(8, Pin.OUT)
inp = Input(9)

kb = None  # Keyboard instance (lazy-created)

# DRAW: show menu (paging handled by display.display_lines)
def draw_menu():
    global current
    # New display_lines knows how to page when given highlight index
    display.display_lines(PHRASES, highlight=current)

# =========================
# MENU MODE HANDLERS
# =========================

# BUTTON: short press = next preset item
def on_click_menu():
    global current
    current = (current + 1) % len(PHRASES)
    draw_menu()

# BUTTON: double-click in menu = enter keyboard mode
def on_double_menu():
    enter_keyboard_mode()

# BUTTON: long press = send preset message (index-based)
def on_long_menu():
    idx = current
    display.notify("Sending...", ms=300)
    bus.send_index(idx)     # <— send preset index to other devices
    led.value(1)
    draw_menu()             # back to menu
    time.sleep_ms(500)
    led.value(0)

def set_menu_handlers():
    """Wire the button Input to menu mode handlers."""
    inp.on_click = on_click_menu
    inp.on_double_click = on_double_menu
    inp.on_long_click = on_long_menu

# =========================
# KEYBOARD MODE
# =========================

def enter_keyboard_mode():
    """Switch to keyboard mode so user can type a custom message."""
    global mode, kb
    mode = MODE_KEYBOARD

    # Lazy-create keyboard on first use
    if kb is None:
        # max_len=14 to fit width (5px * 14 chars = 70px)
        kb = Keyboard(inp, display, max_len=14)

        def kb_enter(text):
            send_custom_message(text)

        kb.on_enter = kb_enter
    else:
        kb.reset()

    # Keyboard.__init__ already wires Input to itself the first time,
    # so on first entry we don't need extra wiring beyond creating kb.

def send_custom_message(text):
    """Called when keyboard ENTER is pressed."""
    global mode
    text = (text or "").strip()
    if not text:
        # Empty -> just go back to menu
        mode = MODE_MENU
        set_menu_handlers()
        draw_menu()
        return

    display.notify("Sending...", ms=300)
    # send as text over BLE
    bus.send_text(text)
    led.value(1)
    time.sleep_ms(500)
    led.value(0)

    # Back to menu mode
    mode = MODE_MENU
    set_menu_handlers()
    draw_menu()

# =========================
# RECEIVE HANDLERS
# =========================

def on_receive_index(idx):
    """Handle incoming index-based message."""
    if 0 <= idx < len(PHRASES):
        msg = "Msg " + PHRASES[idx]
    else:
        msg = "Msg #" + str(idx)
    led.value(1)
    display.notify(msg)
    led.value(0)
    draw_menu()

def on_receive_text(text):
    """Handle incoming text-based message."""
    # Show up to 14 chars to fit the display width
    msg = "RX: " + (text or "")[:14]
    led.value(1)
    display.notify(msg)
    led.value(0)
    draw_menu()

def main():
    global mode
    mode = MODE_MENU

    # Button + BLE setup
    set_menu_handlers()
    bus.on_index = on_receive_index
    bus.on_text = on_receive_text
    bus.start_scan()
    bus.presence()  # optional "hello" burst

    # Brief instructions on screen
    display.fill(0)
    display.small_text("Scout Messenger", 0, 0)
    display.small_text("Click: next",     0, 8)
    display.small_text("Hold: send",      0, 16)
    display.small_text("Dbl: keyboard",   0, 24)
    display.show()
    time.sleep_ms(2500)

    # Start in menu mode
    draw_menu()
    while True:
        time.sleep_ms(50)  # work happens in IRQ/BLE callbacks

if __name__ == "__main__":
    main()
