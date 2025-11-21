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
_current_index = 0

_run_requested = False
_run_module = None
_exit_requested = False

APPS = []

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
        items.append((label, label))

    items.sort(key=lambda x: x[0].lower() if isinstance(x, tuple) else x.lower())
    # Add an Exit option at the end
    items.append(("Exit", "EXIT"))
    return items

# ----------------------------------------------------------
# Drawing helpers
# ----------------------------------------------------------
def _draw_menu():
    global APPS
    """Draw the list with the current selection highlighted."""
    global _display, _current_index
    APPS = discover_programs()
    labels = [label for (label, _mod) in APPS]
    # display_lines(lines, highlight=index) already exists in SmallDisplay
    _display.display_lines(labels, highlight=_current_index)


# ----------------------------------------------------------
# Button handlers
# ----------------------------------------------------------
def _on_click():
    """Short click: move to next app."""
    global _current_index
    _current_index = (_current_index + 1) % len(APPS)
    _draw_menu()

def _on_long_click():
    """Long click: request running the currently highlighted app."""
    global _run_requested, _run_module, _exit_requested
    label, module_name = APPS[_current_index]
    if module_name == "EXIT":
        # Request to exit the menu
        _exit_requested = True
        _display.display_message(["Exiting menu"], delay_ms=400)
    else:    
        _run_requested = True
        _run_module = module_name
        _display.display_message(["Running:", label], delay_ms=400)

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
    global _run_requested, _run_module, _exit_requested
    _run_requested = False
    _run_module = None
    while not _exit_requested:
        if _run_requested and _run_module:
            module_name = _run_module
            _run_requested = False
            _run_module = None
            _run_app(module_name)
            # When the app returns, redraw menu
            _draw_menu()

        # small sleep so we’re not busy-looping
        time.sleep_ms(50)


# ----------------------------------------------------------
# Main menu
# ----------------------------------------------------------
def main():
    global _display, _current_index

    _display = SmallDisplay()

    # Set up the single-button Input (pin 9, active low by default)
    btn = Input(pin_no=9)
    btn.on_click = _on_click
    btn.on_long_click = _on_long_click
    # We’re not using double-click here, so leave btn.on_double_click as None

    _current_index = 0
    _run_app('logo')
    _display.display_message(["ESP32 Menu", "Click=move", "Long click=run"], delay_ms=2000)
    _draw_menu()
    _main_loop()
    _display.fill(0)
    _display.show()

# Run menu on boot
if __name__ == "__main__":
    main()
