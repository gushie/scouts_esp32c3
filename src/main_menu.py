# main.py - boot menu using simple_esp SmallDisplay + Input on ESP32-C3
#
# Short click  = next item
# Long click   = run selected item
#
# Each app (smile.py, message.py, flappybird.py, clock.py, impossible_tetris.py)
# should define a main() function.

from simple_esp import SmallDisplay, Input
import time, sys, gc, os

# ----------------------------------------------------------
# Globals used by callbacks + main loop
# ----------------------------------------------------------
_display = None
_btn = None

EXCLUDED_FILES = {
    "boot.py",
    "main.py",
    "main_menu.py",
    "simple_esp.py",
    "sh1106.py",
}

def discover_programs():
    items = []
    for name in os.listdir():        # root of ESP32 filesystem
        if not name.endswith(".py"):
            continue
        if name in EXCLUDED_FILES:
            continue

        label = name[:-3]           # strip ".py"
        items.append(label)

    items.sort(key=lambda x: x[0].lower() if isinstance(x, tuple) else x.lower())
    # Add an Exit option at the end
    items.insert(0, "Exit")
    return items

# ----------------------------------------------------------
# Drawing helpers
# ----------------------------------------------------------
def _draw_menu():
    """Draw the list with the current selection highlighted."""
    apps = discover_programs()
    current_index = _display.menu(apps, _btn)
    return apps[current_index]
# ----------------------------------------------------------
# Dynamic app loader
# ----------------------------------------------------------
def _run_app(module_name):
    """
    Import and run module_name.main().
    Only imported on demand; then freed afterwards.
    """
    global _display

    # Make sure we reload from flash if it was imported before
    if module_name in sys.modules:
        del sys.modules[module_name]
        gc.collect()

    _display.display_message(["Loading...", module_name], delay_ms=300)

    try:
        mod = __import__(module_name)
    except Exception as e:
        _display.display_message(["Import error", module_name, str(e)[:14]], delay_ms=2500)
        return

    if hasattr(mod, "main"):
        try:
            # If you ever want to share the same display with the app:
            # mod.main(_display)
            mod.main()
        except Exception as e:
            _display.display_message(["Crash in app", module_name, str(e)[:14]], delay_ms=3000)
    else:
        _display.display_message(["No main()", module_name], delay_ms=2000)

    # Free the module after it returns
    try:
        del mod
    except:
        pass
    gc.collect()

def _main_loop():
    module_name = None
    while module_name != "Exit":
        module_name = _draw_menu()
        if module_name != "Exit":
            _display.display_message(["Running:", module_name], delay_ms=400)
            _run_app(module_name)
            

# ----------------------------------------------------------
# Main menu
# ----------------------------------------------------------
def main():
    global _display, _btn

    _display = SmallDisplay()
    _display.hard_reset()
    _btn = Input(pin_no=9)

    _run_app('logo')
    _display.display_message(["ESP32 Menu", "Click=move", "Hold=move up", "Dbl click=run"], delay_ms=2000)
    _main_loop()
    _display.display_message(["Exiting menu"], delay_ms=400)
    _display.fill(0)
    _display.show()

# Run menu on boot
if __name__ == "__main__":
    main()
