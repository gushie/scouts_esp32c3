
# simple_esp.py — ESP32-C3 Helper Library  
**Display • Input Button • BLE Messaging • ASCII Art • Servos • Wi-Fi • Robot**

A lightweight MicroPython helper library designed for ESP32‑C3 projects.  
Includes:

- 72×40 SH1106 mini-window renderer  
- Single-button input (click / double / long)  
- On-screen keyboard  
- BLE presence / index / text messaging  
- Servo + differential-drive robot helpers  
- Wi-Fi helper  
- Lazy imports & reusable framebuffers

---

# 1. SmallDisplay (72×40 SH1106 Window)

## Example
```python
from simple_esp import SmallDisplay
import time

d = SmallDisplay()

d.fill(0)
d.rect(0, 0, 72, 40, 1)
d.small_text_center("MENU", 2)

items = ["Start", "Options", "About", "Exit"]
d.display_lines(items, highlight=1)

d.notify("Saved OK", 1000)

art = """
  XX
 XXXX
XXXXXX
 XXXX
  XX
"""

fb = d.create_image(art)
d.fill(0)
d.image(fb, 0, 0)
d.show()
```

---

## Constructor
### `SmallDisplay()`
Creates a 72×40 drawing window mapped onto an SH1106 128×64 OLED.  
**Pins:** SCL=6, SDA=5.  
**I²C address:** 0x3C.

---

## Drawing Primitives
- `fill(c)`
- `pixel(x, y, c)`
- `rect(x, y, w, h, c)`
- `fill_rect(x, y, w, h, c)`
- `hline(x, y, w, c=1)`
- `vline(x, y, h, c=1)`
- `line(x0, y0, x1, y1, c=1)`
- `ellipse(x, y, xr, yr, color)`
- `scroll(x, y)`
- `show()`

---

## Text Helpers
### `small_text(s, x, y)`  
5×7 font, 14 characters fit across screen.

### `small_text_center(s, y, show=False, reset=False)`  
Center horizontally.

### `notify(text, ms=1500)`  
Clear → show → delay → return.

### `display_lines(lines, highlight=None)`  
5-line menu with optional highlight cursor.

---

## ASCII Art Renderer
### `create_image(s, target_w=72, target_h=40, scale_to_fit=True, reusable=False)`
Returns a FrameBuffer for displaying ASCII-art graphics.

---

# 2. Input — Single-Button Handler

## Example
```python
from simple_esp import Input
import time

btn = Input(pin_no=9)

def click():
    print("CLICK")

def dbl():
    print("DOUBLE")

def lng():
    print("LONG")

btn.on_click = click
btn.on_double_click = dbl
btn.on_long_click = lng

while True:
    time.sleep(0.1)
```

---

## Constructor
### `Input(pin_no=9, active_low=True, debounce_ms=80, long_ms=500, double_ms=500)`
Interrupt-driven, uses **Timer(0)** for double-click detection.

## Callbacks
- `on_click`
- `on_double_click`
- `on_long_click`

---

# 3. Keyboard — On-screen Text Input

Works with `SmallDisplay` + `Input`.

### Example
```python
kbd = Keyboard(btn, display=d)

def on_enter(text):
    print("Entered:", text)

kbd.on_enter = on_enter
```

### Special Keys
| Character | Meaning |
|----------|---------|
| `+` | ENTER |
| `-` | Backspace |
| `^` | Shift toggle |

### Actions
- Click → next character  
- Double click → next row  
- Long click → select/enter/backspace/shift  

---

# 4. Bluetooth — Simple BLE Messaging

Supports:
- `presence()`
- `send_index(idx)`
- `send_text(text)`
- `start_scan()`

## Example
```python
from simple_esp import Bluetooth
import time

ble = Bluetooth(name="SM")
ble.start_scan()

def got(text):
    print("Got text:", text)

ble.on_message = got

while True:
    ble.send_text('Hello')
    time.sleep(1)
```

---

# 5. Servo

## Example
```python
from simple_esp import Servo
import time

s = Servo(pin=18)
s.angle(0)
s.angle(90)
s.angle(180)
s.deinit()
```

## Constructor
### `Servo(pin, *, freq=50, min_us=500, max_us=2500, stop_us=None)`

## Methods
- `angle(degrees)`
- `center()`
- `speed(value)`  # continuous rotation
- `stop()`
- `deinit()`

---

# 6. Robot — Differential Drive

Controls two continuous servos.

## Example
```python
from simple_esp import Robot, Servo

left = Servo(0, stop_us=1500)
right = Servo(1, stop_us=1500)

bot = Robot(left, right, speed=1)
bot.forward(1)
bot.left(0.5)
bot.stop()
```

## Methods
- `forward(duration=1, speed=None)`
- `backward(duration=1, speed=None)`
- `left(duration=1, speed=None)`
- `right(duration=1, speed=None)`
- `stop()`

---

# 7. Wi-Fi Helper

## Example
```python
from simple_esp import connect_wifi

wlan = connect_wifi("MySSID", "Password")

if wlan:
    print("IP:", wlan.ifconfig()[0])
```

## Function
### `connect_wifi(ssid="scouts", password="greatbarton", timeout=10)`
Connects with auto RTC time sync.

---

# End of Documentation
