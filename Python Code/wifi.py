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

from simple_esp import SmallDisplay, Input, Keyboard, Registry, connect_wifi
import network
import time
import os

# ---- Constants ----

BTN_PIN = 9

MENU_OPTIONS = ["Connect saved", "Connect new"]

# ---- Hardware ----

display = SmallDisplay()
button = Input(BTN_PIN)
registry = Registry()
# ---- Helpers: file I/O ----

def load_saved_wifi():
    """Return (ssid, password) from registry.json, or (None, None) if missing/invalid."""
    global registry
    ssid = registry.get('wifi.ssid')
    password = registry.get('wifi.password')
    return ssid, password


def save_wifi(ssid, password):
    """Save (ssid, password) to registry.json."""
    global registry
    registry.set('wifi.ssid', ssid)
    registry.set('wifi.password', password)

# ---- Mode 1: menu selection ----

def choose_menu_option():
    """Show menu and return chosen index (0 or 1)."""
    display.fill(0)
    display.small_text("WiFi setup", 0, 0)
    display.small_text("Click: next", 0, 8)
    display.small_text("Dbl clk: select", 0, 16)
    display.show()
    time.sleep_ms(1200)

    return display.menu(MENU_OPTIONS, button)

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

def choose_ssid():
    """Scan for networks, let user choose one, return SSID or None."""

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

    if not names:
        display.notify("No networks", ms=1500)
        return None

    return names[display.menu(names, button)]


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

    kb = Keyboard(button, display, max_len=32, on_enter=on_enter)
    kb.open()

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


if __name__ == "__main__":
    main()
