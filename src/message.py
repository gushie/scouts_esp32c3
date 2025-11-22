# message.py — Simple Bluetooth Messenger with usernames
#
# Behaviour:
#   - On startup, we send a "discover" message.
#   - Other devices reply with their username (one reply, no loops).
#   - Screen shows list of:
#        ALL
#        user1
#        user2
#        ...
#   - Click         : move to next name
#   - Double-click  : send a message to selected name (opens keyboard)
#   - Long press    : change your own username (opens keyboard)
#
# Messages are sent as:
#   sender|target|kind|payload
# where:
#   sender = username of sender
#   target = "*" (for ALL) or a specific username
#   kind   = "D" (discover), "I" (identity), "M" (message)
#   payload= text (for "M"), empty for "D" and "I"

from simple_esp import Input, SmallDisplay, Bluetooth, Keyboard, Registry
from machine import Pin
import time

# ---------------------------
# MODES
# ---------------------------
MODE_MENU      = 0   # choosing who to send to
MODE_MESSAGE   = 1   # typing a message
MODE_SET_NAME  = 2   # typing our username

mode = MODE_MENU
current_index = 0     # which item in the target list is highlighted

# ---------------------------
# BLUETOOTH + DISPLAY + INPUT
# ---------------------------
bus = Bluetooth()
display = SmallDisplay()
registry = Registry()
led = Pin(8, Pin.OUT)
inp = Input(9)
kb = Keyboard(inp, display, max_len=14)

# ---------------------------
# USERNAMES AND TARGETS
# ---------------------------
username = None          # our own username (string)
known_users = set()      # usernames of other devices we have seen
current_target = "ALL"   # who we are sending to ("ALL" or a username)


# =========================================================
# USERNAME + REGISTRY HELPERS
# =========================================================
def load_username_from_registry():
    """Try to load our username from REGISTRY."""
    global username, registry
    stored = registry.get("msg.username", "")
    username = stored or None

def auto_assign_username():
    """
    If we don't have a username, pick the lowest integer "1", "2", "3", ...
    that is NOT already used by other known users.
    """
    global username, registry
    used = set(known_users)   # usernames we have seen

    num = 1
    while str(num) in used:
        num += 1

    username = str(num)
    registry.set("msg.username", username)

def ensure_username():
    """Make sure username is set to something sensible."""
    if username:
        return
    load_username_from_registry()
    if username:
        return
    auto_assign_username()

def remember_user(name):
    """Remember a username we saw in a message."""
    if not name:
        return
    if name == username:
        return
    known_users.add(name)

# =========================================================
# TARGET LIST + MENU
# =========================================================
def get_targets():
    """
    Build the list of things we can send to:
      ["ALL", user1, user2, ...]
    """
    # Sort the names so the list is stable and easy to scan
    others = sorted(u for u in known_users if u != username)
    return ["ALL"] + others

def draw_menu():
    """
    Draw the menu showing:
      Me: <username>
      To: <current_target>
      and a list of all targets (ALL + usernames).
    """
    ensure_username()
    name = username or "?"

    targets = get_targets()
    if not targets:
        # Should always have at least ALL; just in case:
        targets = ["ALL"]

    # Make sure current_index is inside range
    global current_index, current_target
    if current_index >= len(targets):
        current_index = 0

    current_target = targets[current_index]

    header_lines = [
        "Me: " + name,
        "To: " + current_target,
        ""  # blank line before list
    ]
    all_lines = header_lines + targets

    # Highlight the selected target line
    highlight_index = len(header_lines) + current_index

    display.display_lines(all_lines, highlight=highlight_index)


# =========================================================
# PACKET FORMAT: sender|target|kind|payload
# =========================================================
def build_packet(kind, payload, to_name=None):
    """
    Build a packet string to send over Bluetooth:
      sender|target|kind|payload
    - kind: "D" (discover), "I" (identity), "M" (message)
    - target: "*" for ALL or specific username
    """
    ensure_username()
    sender = username

    if to_name is None or to_name == "ALL":
        target = "*"   # broadcast
    else:
        target = to_name

    return "{}|{}|{}|{}".format(sender, target, kind, payload)

def parse_packet(text):
    """Split incoming text into (sender, target, kind, payload) or None."""
    parts = (text or "").split("|", 3)
    if len(parts) != 4:
        return None
    sender, target, kind, payload = parts
    return sender, target, kind, payload

def send_discover():
    """
    Ask "who is out there?".
    Others will respond ONCE with an identity packet.
    """
    pkt = build_packet("D", "", to_name="ALL")
    bus.send_text(pkt)

def send_identity(to_name=None):
    """
    Tell others our username.
    If to_name is None or "ALL", broadcast to everyone.
    Otherwise send just to that username.
    """
    pkt = build_packet("I", "", to_name=to_name)
    bus.send_text(pkt)

def enter_message_mode(target_name):
    """
    Switch to keyboard mode to type a message to target_name.
    """
    global mode, current_target, kb
    mode = MODE_MESSAGE
    current_target = target_name

    def kb_enter_message(text):
        send_message(text)

    kb.on_enter = kb_enter_message
    kb.open()

def enter_set_name_mode():
    """
    Switch to keyboard mode to set our username.
    """
    global mode, kb, username
    mode = MODE_SET_NAME

    def kb_enter_name(text):
        set_username(text)

    kb.on_enter = kb_enter_name
    kb.open(text=username)

# =========================================================
# SENDING MESSAGES
# =========================================================
def send_message(text):
    """
    Called when keyboard ENTER is pressed in message mode.
    Sends text to current_target.
    """
    global mode
    text = (text or "").strip()
    if not text:
        # Empty -> go back to menu
        mode = MODE_MENU
        set_menu_handlers()
        draw_menu()
        return

    pkt = build_packet("M", text, to_name=current_target)

    display.notify("Sending...", ms=300)
    print(pkt)
    bus.send_text(pkt)
    led.value(1)
    time.sleep_ms(300)
    led.value(0)

    # Back to menu
    mode = MODE_MENU
    set_menu_handlers()
    draw_menu()

def set_username(text):
    """
    Called when keyboard ENTER is pressed in set-name mode.
    Saves username (or auto-picks a number if left blank),
    then broadcasts our identity.
    """
    global mode, username, registry
    name = (text or "").strip()

    if name:
        username = name
        registry.set("msg.username", username)
    else:
        # If user leaves it blank, auto-pick a number
        auto_assign_username()

    # Tell others our name
    send_identity(to_name="ALL")

    # Back to menu
    mode = MODE_MENU
    set_menu_handlers()
    draw_menu()

# =========================================================
# MENU BUTTON HANDLERS
# =========================================================
def on_click_menu():
    """Short click in menu: move to next target in the list."""
    global current_index
    targets = get_targets()
    if not targets:
        targets = ["ALL"]

    current_index = (current_index + 1) % len(targets)
    draw_menu()

def on_double_menu():
    """Double-click: open keyboard to send message to selected target."""
    targets = get_targets()
    if not targets:
        targets = ["ALL"]

    # Make sure index is valid
    global current_index
    if current_index >= len(targets):
        current_index = 0

    target_name = targets[current_index]
    enter_message_mode(target_name)

def on_long_menu():
    """Long press: change our username."""
    enter_set_name_mode()

def set_menu_handlers():
    """Wire the Input callbacks for menu mode."""
    inp.on_click = on_click_menu
    inp.on_double_click = on_double_menu
    inp.on_long_click = on_long_menu

def on_receive_text(text):
    """
    Handle incoming text-based messages:
      sender|target|kind|payload
    """
    parsed = parse_packet(text)
    if not parsed:
        return

    sender, target, kind, payload = parsed
    remember_user(sender)

    ensure_username()

    # ---------- DISCOVER ("D") ----------
    if kind == "D":
        # Someone is asking "who is there?"
        # Remember them and reply with our identity (once per discover packet)
        remember_user(sender)
        send_identity(to_name=sender)
        draw_menu()
        return

    # ---------- IDENTITY ("I") ----------
    if kind == "I":
        # Someone is telling us their username.
        # Only care if it's broadcast or aimed at us.
        if target in ("*", username):
            remember_user(sender)
            draw_menu()
        return

    # ---------- MESSAGE ("M") ----------
    if kind == "M":
        # Only display if:
        #   - it's broadcast ("*"), or
        #   - it's directly addressed to us
        if target not in ("*", username):
            return

        msg = "{}: {}".format(sender, payload or "")
        msg = msg[:14]  # fit screen

        led.value(1)
        display.notify(msg)
        led.value(0)
        draw_menu()
        return

    # Unknown kind: ignore silently or show raw
    # Here we ignore to keep it simple.


# =========================================================
# MAIN
# =========================================================
def main():
    global mode
    mode = MODE_MENU

    # Get username ready
    load_username_from_registry()
    ensure_username()

    # Button + BLE setup
    set_menu_handlers()
    bus.on_text = on_receive_text
    bus.start_scan()
    bus.presence()   # low-level presence
    send_discover()  # high-level "who is there?"

    # Brief instructions
    display.fill(0)
    display.small_text("Scout Messenger", 0, 0)
    display.small_text("Click: next user", 0, 8)
    display.small_text("Dbl: send msg",    0, 16)
    display.small_text("Hold: set name",   0, 24)
    display.show()
    time.sleep_ms(2500)

    draw_menu()

    while True:
        time.sleep_ms(50)  # everything else happens in callbacks/IRQs


if __name__ == "__main__":
    main()
