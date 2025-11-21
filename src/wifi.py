# wifi_setup.py — Simple Wi-Fi configurator using simple_esp
#
# Menu:
#   - Connect saved
#   - Connect new
#
# Connect saved:
#   - Reads wifi.txt (format: SSID \t PASSWORD \n)
#   - Attempts to connect
#   - Exits, leaving Wi-Fi connected
#
# Connect new:
#   - Scans for networks
#   - Lets user pick SSID with button
#   - Prompts for password using Keyboard
#   - Saves to wifi.txt
#   - Attempts to connect
#   - Exits, leaving Wi-Fi connected

from simple_esp import SmallDisplay, Input, Keyboard
import network
import time
import os

# ---- Constants ----

WIFI_FILE = "wifi.txt"
BTN_PIN = 9

MENU_OPTIONS = ["Connect saved", "Connect new"]


# ---- Hardware ----

display = SmallDisplay()
button = Input(BTN_PIN)


# ---- Helpers: file I/O ----

def load_saved_wifi():
    """Return (ssid, password) from wifi.txt, or (None, None) if missing/invalid."""
    try:
        if WIFI_FILE not in os.listdir():
            return None, None
    except:
        # No filesystem or error
        return None, None

    try:
        with open(WIFI_FILE, "r") as f:
            line = f.readline().rstrip("\n")
    except:
        return None, None

    if not line:
        return None, None

    # format: SSID \t PASSWORD
    parts = line.split("\t", 1)
    if len(parts) != 2:
        return None, None
    ssid, pw = parts[0], parts[1]
    if not ssid:
        return None, None
    return ssid, pw


def save_wifi(ssid, password):
    """Save (ssid, password) to wifi.txt."""
    try:
        with open(WIFI_FILE, "w") as f:
            f.write(ssid + "\t" + password + "\n")
    except:
        # Simple ignore on error; user will see connect fail anyway
        pass


# ---- Helpers: Wi-Fi connect ----

def connect_wifi(ssid, password, timeout=15):
    """Try to connect to given Wi-Fi. Returns True on success."""
    sta = network.WLAN(network.STA_IF)
    sta.active(True)

    # If already connected to this SSID, just keep it
    if sta.isconnected():
        try:
            cfg = sta.config("essid")
        except:
            cfg = None
        if isinstance(cfg, bytes):
            cfg = cfg.decode()

        if cfg == ssid:
            return True

    sta.disconnect()
    display.notify("Connecting...", ms=500)

    sta.connect(ssid, password)

    t0 = time.ticks_ms()
    while not sta.isconnected():
        if time.ticks_diff(time.ticks_ms(), t0) > timeout * 1000:
            break
        time.sleep_ms(200)

    if sta.isconnected():
        ip = sta.ifconfig()[0]
        display.notify("OK " + ip, ms=1500)
        return True
    else:
        display.notify("Failed", ms=1500)
        return False


# ---- Mode 1: menu selection ----

_menu_choice = 0
_menu_done = False

def _draw_menu():
    display.display_lines(MENU_OPTIONS, highlight=_menu_choice)

def _menu_click():
    global _menu_choice
    _menu_choice = (_menu_choice + 1) % len(MENU_OPTIONS)
    _draw_menu()

def _menu_long():
    global _menu_done
    _menu_done = True

def choose_menu_option():
    """Show menu and return chosen index (0 or 1)."""
    global _menu_choice, _menu_done
    _menu_choice = 0
    _menu_done = False

    button.on_click = _menu_click
    button.on_double_click = None
    button.on_long_click = _menu_long

    display.fill(0)
    display.small_text("WiFi setup", 0, 0)
    display.small_text("Click: next", 0, 8)
    display.small_text("Hold: select", 0, 16)
    display.show()
    time.sleep_ms(1200)

    _draw_menu()

    while not _menu_done:
        time.sleep_ms(50)

    return _menu_choice


# ---- Mode 2: connect to saved Wi-Fi ----

def run_connect_saved():
    ssid, pw = load_saved_wifi()
    if not ssid:
        display.notify("No saved WiFi", ms=1500)
        return False

    display.notify("Saved: " + ssid[:10], ms=1000)
    ok = connect_wifi(ssid, pw)
    return ok


# ---- Mode 3: scan, choose SSID, enter password ----

_ssid_list = []
_ssid_idx = 0
_ssid_done = False
_ssid_selected = None

def _draw_ssid_list():
    if not _ssid_list:
        display.notify("No networks", ms=1500)
        return
    display.display_lines(_ssid_list, highlight=_ssid_idx)

def _ssid_click():
    global _ssid_idx
    if not _ssid_list:
        return
    _ssid_idx = (_ssid_idx + 1) % len(_ssid_list)
    _draw_ssid_list()

def _ssid_long():
    global _ssid_done, _ssid_selected
    if not _ssid_list:
        _ssid_done = True
        _ssid_selected = None
        return
    _ssid_selected = _ssid_list[_ssid_idx]
    _ssid_done = True

def choose_ssid():
    """Scan for networks, let user choose one, return SSID or None."""
    global _ssid_list, _ssid_idx, _ssid_done, _ssid_selected

    display.notify("Scanning...", ms=800)

    sta = network.WLAN(network.STA_IF)
    sta.active(True)

    try:
        raw = sta.scan()
    except:
        display.notify("Scan error", ms=1500)
        return None

    # raw: list of (ssid, bssid, channel, RSSI, authmode, hidden)
    names = []
    seen = set()
    for item in raw:
        ssid_bytes = item[0]
        try:
            name = ssid_bytes.decode()
        except:
            continue
        name = name.strip()
        if not name:
            continue
        if name in seen:
            continue
        seen.add(name)
        names.append(name)

    names.sort()
    _ssid_list = names
    _ssid_idx = 0
    _ssid_done = False
    _ssid_selected = None

    button.on_click = _ssid_click
    button.on_double_click = None
    button.on_long_click = _ssid_long

    if not _ssid_list:
        display.notify("No networks", ms=1500)
        return None

    display.notify("Click/hold", ms=800)
    _draw_ssid_list()

    while not _ssid_done:
        time.sleep_ms(50)

    return _ssid_selected


def enter_password_for(ssid):
    """Prompt for password using Keyboard; return the entered password (string)."""
    pwd_holder = {"done": False, "pwd": ""}

    def on_enter(text):
        pwd_holder["pwd"] = text
        pwd_holder["done"] = True

    # Show prompt
    display.fill(0)
    display.small_text("SSID:", 0, 0)
    display.small_text(ssid[:14], 0, 8)
    display.small_text("Enter password", 0, 16)
    display.show()
    time.sleep_ms(800)

    kb = Keyboard(button, display, max_len=32)
    kb.on_enter = on_enter

    while not pwd_holder["done"]:
        time.sleep_ms(50)

    # After ENTER, Keyboard restored previous Input handlers (SSID select),
    # but we're done here anyway.
    return pwd_holder["pwd"]


def run_connect_new():
    ssid = choose_ssid()
    if not ssid:
        return False

    pwd = enter_password_for(ssid)
    if pwd is None:
        return False

    # Save credentials
    save_wifi(ssid, pwd)

    # Try connecting
    ok = connect_wifi(ssid, pwd)
    return ok


# ---- Main ----

def main():
    choice = choose_menu_option()

    if choice == 0:
        run_connect_saved()
    else:
        run_connect_new()

    # Exit; leave Wi-Fi in whatever state it ended up in
    display.notify("Done", ms=800)
    import main_menu
    main_menu.main()

if __name__ == "__main__":
    main()
