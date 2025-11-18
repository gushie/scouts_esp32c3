# simple_esp.py — ESP32-C3 helpers for 72x40 SH1106 display, buttons, servos and bluetooth BLE
# - Timers: Input=Timer(0), BLE=Timer(1)
# - 14-char truncation

from machine import Pin, Timer, unique_id
import time

try:
    import micropython
    _SCHEDULE = micropython.schedule
except:
    _SCHEDULE = None

_pwm = None
def _ensure_pwm():
    global _pwm
    if _pwm is None:
        from machine import PWM
        _pwm = PWM
    return _pwm

_network = None
def _ensure_network():
    global _network
    if _network is None:
        import network
        _network = network
    return _network

_ntptime = None
def _ensure_ntptime():
    global _ntptime
    if _ntptime is None:
        import ntptime
        _ntptime = ntptime
    return _ntptime

_framebuf = None
def _ensure_framebuf():
    global _framebuf
    if _framebuf is None:
        import framebuf
        _framebuf = framebuf
    return _framebuf

_SH1106_I2C = None
def _ensure_sh1106():
    global _SH1106_I2C
    if _SH1106_I2C is None:
        from sh1106 import SH1106_I2C
        _SH1106_I2C = SH1106_I2C
    return _SH1106_I2C

_I2C = None
def _ensure_i2c():
    global _I2C
    if _I2C is None:
        from machine import I2C
        _I2C = I2C
    return _I2C

_FONT5X7 = None

def _ensure_font():
    global _FONT5X7
    if _FONT5X7 is None:
        _FONT5X7 = (
            b"\x00\x00\x00\x00\x00" b"\x00\x00\x5F\x00\x00" b"\x00\x07\x00\x07\x00" b"\x14\x7F\x14\x7F\x14"
            b"\x24\x2A\x7F\x2A\x12" b"\x23\x13\x08\x64\x62" b"\x36\x49\x55\x22\x50" b"\x00\x05\x03\x00\x00"
            b"\x00\x1C\x22\x41\x00" b"\x00\x41\x22\x1C\x00" b"\x14\x08\x3E\x08\x14" b"\x08\x08\x3E\x08\x08"
            b"\x00\x50\x30\x00\x00" b"\x08\x08\x08\x08\x08" b"\x00\x60\x60\x00\x00" b"\x20\x10\x08\x04\x02"
            b"\x3E\x51\x49\x45\x3E" b"\x00\x42\x7F\x40\x00" b"\x42\x61\x51\x49\x46" b"\x21\x41\x45\x4B\x31"
            b"\x18\x14\x12\x7F\x10" b"\x27\x45\x45\x45\x39" b"\x3C\x4A\x49\x49\x30" b"\x01\x71\x09\x05\x03"
            b"\x36\x49\x49\x49\x36" b"\x06\x49\x49\x29\x1E" b"\x00\x36\x36\x00\x00" b"\x00\x56\x36\x00\x00"
            b"\x08\x14\x22\x41\x00" b"\x14\x14\x14\x14\x14" b"\x00\x41\x22\x14\x08" b"\x02\x01\x51\x09\x06"
            b"\x32\x49\x79\x41\x3E" b"\x7E\x11\x11\x11\x7E" b"\x7F\x49\x49\x49\x36" b"\x3E\x41\x41\x41\x22"
            b"\x7F\x41\x41\x22\x1C" b"\x7F\x49\x49\x49\x41" b"\x7F\x09\x09\x09\x01" b"\x3E\x41\x49\x49\x7A"
            b"\x7F\x08\x08\x08\x7F" b"\x00\x41\x7F\x41\x00" b"\x20\x40\x41\x3F\x01" b"\x7F\x08\x14\x22\x41"
            b"\x7F\x40\x40\x40\x40" b"\x7F\x02\x04\x02\x7F" b"\x7F\x04\x08\x10\x7F" b"\x3E\x41\x41\x41\x3E"
            b"\x7F\x09\x09\x09\x06" b"\x3E\x41\x51\x21\x5E" b"\x7F\x09\x19\x29\x46" b"\x46\x49\x49\x49\x31"
            b"\x01\x01\x7F\x01\x01" b"\x3F\x40\x40\x40\x3F" b"\x1F\x20\x40\x20\x1F" b"\x7F\x20\x10\x20\x7F"
            b"\x63\x14\x08\x14\x63" b"\x07\x08\x70\x08\x07" b"\x61\x51\x49\x45\x43" b"\x00\x7F\x41\x41\x00"
            b"\x02\x04\x08\x10\x20" b"\x00\x41\x41\x7F\x00" b"\x04\x02\x01\x02\x04" b"\x40\x40\x40\x40\x40"
            b"\x00\x03\x07\x00\x00" b"\x20\x54\x54\x54\x78" b"\x7F\x48\x44\x44\x38" b"\x38\x44\x44\x44\x20"
            b"\x38\x44\x44\x48\x7F" b"\x38\x54\x54\x54\x18" b"\x08\x7E\x09\x01\x02" b"\x0C\x52\x52\x52\x3E"
            b"\x7F\x08\x04\x04\x78" b"\x00\x44\x7D\x40\x00" b"\x20\x40\x44\x3D\x00" b"\x7F\x10\x28\x44\x00"
            b"\x00\x41\x7F\x40\x00" b"\x7C\x04\x18\x04\x78" b"\x7C\x08\x04\x04\x78" b"\x38\x44\x44\x44\x38"
            b"\x7C\x14\x14\x14\x08" b"\x08\x14\x14\x18\x7C" b"\x7C\x08\x04\x04\x08" b"\x48\x54\x54\x54\x20"
            b"\x04\x3F\x44\x40\x20" b"\x3C\x40\x40\x20\x7C" b"\x1C\x20\x40\x20\x1C" b"\x3C\x40\x30\x40\x3C"
            b"\x44\x28\x10\x28\x44" b"\x0C\x50\x50\x50\x3C" b"\x44\x64\x54\x4C\x44" b"\x00\x08\x36\x41\x00"
            b"\x00\x00\x7F\x00\x00" b"\x00\x41\x36\x08\x00" b"\x02\x01\x02\x04\x02"
        )
    return _FONT5X7

# Reusable buffers for ASCII → framebuffer conversion
_FB_SRC = None
_FB_SCALED = None
_FB_DST = None
def _ensure_buffers(src_w, src_h, target_w, target_h):
    global _FB_SRC, _FB_SCALED, _FB_DST

    # Bytes needed for a given width/height in MONO_VLSB
    def need_bytes(w, h):
        return w * ((h + 7) // 8)

    # --- Source buffer ---
    need_src = need_bytes(src_w, src_h)
    if _FB_SRC is None or len(_FB_SRC) < need_src:
        _FB_SRC = bytearray(need_src)

    # --- Scaled buffer (worst case same size as source) ---
    need_scaled = need_bytes(src_w, src_h)
    if _FB_SCALED is None or len(_FB_SCALED) < need_scaled:
        _FB_SCALED = bytearray(need_scaled)

    # --- Destination buffer (only ever one size: 72×40) ---
    need_dst = need_bytes(target_w, target_h)
    if _FB_DST is None or len(_FB_DST) < need_dst:
        _FB_DST = bytearray(need_dst)

    return _FB_SRC, _FB_SCALED, _FB_DST

# ---------------------------------------------------------------------------
# SmallDisplay — 72x40 window on SH1106 128x64 (col_offset=28, y_offset=24)
# ---------------------------------------------------------------------------
class SmallDisplay:
    SCL, SDA, ADDR = 6, 5, 0x3C

    def __init__(self):
        SH1106_I2C = _ensure_sh1106()
        try:
            self.hard_reset()
        except Exception:
            pass
        try:
            i2c = self.new_i2c()
            self.driver = SH1106_I2C(128, 64, i2c, addr=self.ADDR, col_offset=28)
        except Exception:
            self.driver = None

        self.x_offset = 0
        self.y_offset = 24
        self.width, self.height = 72, 40
        self.fill(0)

    def new_i2c(self):
        I2C = _ensure_i2c()
        return I2C (0, scl=Pin(self.SCL), sda=Pin(self.SDA), freq=100000)

    def hard_reset(self):
        def reset_pins():
            scl = Pin(self.SCL, Pin.OUT, value=1)
            sda = Pin(self.SDA, Pin.IN)
            for _ in range(9):
                scl.value(0); scl.value(1)

        reset_pins()
        i2c = self.new_i2c()

        def cmd(c):
            i2c.writeto(self.ADDR, bytes((0x80, c)))

        # Safe-ish init
        for c in (0xAE, 0x20,0x00, 0x40, 0xA1, 0xC8, 0xA8,0x3F, 0xD3,0x00,
                  0xDA,0x12, 0xD5,0x80, 0xD9,0xF1, 0xDB,0x40, 0x8D,0x14, 0xA6, 0xAF):
            cmd(c)

    # --- primitives bounded to 72x40
    def fill(self, c):
        if self.driver:
            self.driver.framebuf.fill_rect(self.x_offset, self.y_offset, self.width, self.height, c)

    def pixel(self, x, y, c):
        if self.driver and 0 <= x < self.width and 0 <= y < self.height:
            self.driver.pixel(x + self.x_offset, y + self.y_offset, c)

    def rect(self, x, y, w, h, c):
        if self.driver:
            self.driver.rect(x + self.x_offset, y + self.y_offset, w, h, c)

    def fill_rect(self, x, y, w, h, c):
        if self.driver:
            self.driver.fill_rect(x + self.x_offset, y + self.y_offset, w, h, c)

    def hline(self, x, y, w, c=1):
        if self.driver:
            self.driver.hline(x + self.x_offset, y + self.y_offset, w, c)

    def vline(self, x, y, h, c=1):
        if self.driver:
            self.driver.vline(x + self.x_offset, y + self.y_offset, h, c)

    def line(self, x0, y0, x1, y1, c=1):
        if self.driver:
            x0 += self.x_offset; y0 += self.y_offset
            x1 += self.x_offset; y1 += self.y_offset
            self.driver.line(x0, y0, x1, y1, c)

    def image(self, fbuf, x=0, y=0, key=-1, palette=None):
        if self.driver:
            self.driver.blit(fbuf, x + self.x_offset, y + self.y_offset, key, palette)

    def scroll(self, x, y):
        if self.driver:
            self.driver.scroll(x, y)

    def ellipse(self, x, y, xr, yr, color):
        if self.driver:
            self.driver.ellipse(x + self.x_offset, y + self.y_offset, xr, yr, color)

    def show(self):
        if self.driver:
            self.driver.show()

    # --- text (14 chars fit if we advance 5px/char; no extra spacing)
    def small_text(self, s, x, y):
        print(s)
        if not self.driver:
            return
        px = x
        for ch in s:
            g = self.glyph5x7(ch)
            if g is None:
                px += 5; continue
            b0,b1,b2,b3,b4 = g[0], g[1], g[2], g[3], g[4]
            for cx, byte in ((0,b0),(1,b1),(2,b2),(3,b3),(4,b4)):
                yy = y; m = byte
                for _ in range(7):
                    self.pixel(px+cx, yy, m & 1)
                    m >>= 1; yy += 1
            px += 5  # EXACT 5px advance → 14 chars * 5 = 70px (fits in 72px)

    def small_text_center(self, s, y=16, show=False, reset=False):
        text_w = len(s) * 5  # 5px per char (no extra spacing)
        x = max(0, (self.width - text_w) // 2)
        if reset:
            self.fill(0)
        self.small_text(s, x, y)
        if show:
            self.show()

    def notify(self, text, ms=1500):
        self.fill(0)
        self.small_text(text[:14], 0, 16)  # 14 chars
        self.show()
        time.sleep_ms(ms)

    def display_lines(self, lines, highlight=None):
        page = 0
        if highlight is not None:
            page = highlight // 5      
        start = page * 5
        end = start + 5
        self.fill(0)
        y = 0
        for i, line in enumerate(lines[start:end], start=start):
            if self.driver:
                if highlight is not None and i == highlight:
                    # cursor bar on the highlighted line
                    self.fill_rect(0, y, 2, 8, 1)
                self.small_text(line[:14], 4, y)
            print(("> " if (highlight is not None and i == highlight) else "  ") + line)
            y += 8
        self.show()

    def display_message(self, lines, delay_ms=1500):
        """Utility to show 1–3 centered lines."""
        self.fill(0)

        # lines is a list of strings; we vertically space them by 8px
        start_y = 8 if len(lines) == 1 else 4
        y = start_y
        for line in lines[:3]:
            self.small_text_center(line[:14], y)
            y += 10
        self.show()
        if delay_ms:
            time.sleep_ms(delay_ms)

    def glyph5x7(self, ch):
        font = _ensure_font()    
        o = (ord(ch) - 32) * 5
        if 0 <= o <= len(font) - 5:
            return memoryview(font)[o:o+5]
        return None

        # --- ASCII art to framebuffer 
    def create_image(self, s, target_w=72, target_h=40, scale_to_fit=True, reusable=False):
        framebuf = _ensure_framebuf()

        # Clean input lines
        if s.startswith("\n"):
            s = s[1:]
        lines = [ln.rstrip("\n") for ln in s.splitlines()]
        if not lines:
            if reusable:
                _, _, dst_buf = _ensure_buffers(1, 1, target_w, target_h)
            else:
                dst_buf = bytearray(target_w * ((target_h + 7) // 8))
            return framebuf.FrameBuffer(dst_buf, target_w, target_h, framebuf.MONO_VLSB)

        src_w = max(len(ln) for ln in lines)
        src_h = len(lines)

        def bytes_for(w, h):
            return w * ((h + 7) // 8)

        # Get buffers (either reusable globals or fresh per-call)
        if reusable:
            src_buf, scaled_buf, dst_buf = _ensure_buffers(src_w, src_h, target_w, target_h)
        else:
            src_buf = bytearray(bytes_for(src_w, src_h))
            scaled_buf = None
            dst_buf = None

        # ----- Build source framebuffer -----
        src_fb = framebuf.FrameBuffer(src_buf, src_w, src_h, framebuf.MONO_VLSB)
        src_fb.fill(0)

        for y, ln in enumerate(lines):
            for x, ch in enumerate(ln):
                src_fb.pixel(x, y, 0 if ch == " " else 1)

        # ----- No scaling → just centre directly -----
        if not scale_to_fit:
            if not reusable:
                dst_buf = bytearray(bytes_for(target_w, target_h))
            dst_fb = framebuf.FrameBuffer(dst_buf, target_w, target_h, framebuf.MONO_VLSB)
            dst_fb.fill(0)
            ox = (target_w - src_w) // 2
            oy = (target_h - src_h) // 2
            dst_fb.blit(src_fb, ox, oy)
            return dst_fb

        # ----- Compute scale factor -----
        sx = target_w / src_w
        sy = target_h / src_h
        scale = min(sx, sy)

        new_w = max(1, int(src_w * scale))
        new_h = max(1, int(src_h * scale))

        needed_scaled = bytes_for(new_w, new_h)
        if not reusable or scaled_buf is None or len(scaled_buf) < needed_scaled:
            scaled_buf = bytearray(needed_scaled)

        # ----- Scale into scaled_fb -----
        scaled_fb = framebuf.FrameBuffer(scaled_buf, new_w, new_h, framebuf.MONO_VLSB)
        scaled_fb.fill(0)

        for ny in range(new_h):
            sy_idx = min(src_h - 1, int(ny / scale))
            for nx in range(new_w):
                sx_idx = min(src_w - 1, int(nx / scale))
                scaled_fb.pixel(nx, ny, src_fb.pixel(sx_idx, sy_idx))

        needed_dst = bytes_for(target_w, target_h)
        if not reusable or dst_buf is None or len(dst_buf) < needed_dst:
            dst_buf = bytearray(needed_dst)

        # ----- Blit scaled version centred -----
        dst_fb = framebuf.FrameBuffer(dst_buf, target_w, target_h, framebuf.MONO_VLSB)
        dst_fb.fill(0)

        ox = (target_w - new_w) // 2
        oy = (target_h - new_h) // 2
        dst_fb.blit(scaled_fb, ox, oy)

        return dst_fb

class Keyboard:
    """
    Single-button on-screen keyboard.

    Character layout (4 rows, all visible):

        "+- ABCDEFGH"
        "IJKLMNOPQRS"
        "TUVWXYZ.'?!"
        "0123456789@"

    Controls via Input:

      - single click:
          move to next character; if at end of line, wrap to first character
          of the next line (and wrap from last row back to row 0)

      - double-click:
          move down one row, keeping column if possible

      - long click:
          '+' : ENTER -> calls on_enter(text) and restores previous Input handlers
          '-' : delete last character (backspace)
          other char: append to text (up to max_len) and call on_change(text)

    Display layout (72x40 window):

      y=0  : current text (last 14 chars)
      y=8  : row 0 "+- ABCDEFGH"
      y=16 : row 1 "IJKLMNOPQRS"
      y=24 : row 2 "TUVWXYZ.'?!"
      y=32 : row 3 "0123456789@"
    """

    def __init__(self, button_input, display=None, max_len=14):
        self.input = button_input       # Input instance
        self.display = display          # SmallDisplay instance (optional)
        self.max_len = max_len

        self.rows = [
            "+- ABCDEFGH",
            "IJKLMNOPQRS",
            "TUVWXYZ.'?!",
            "0123456789@",
        ]

        self.row = 0
        self.col = 0
        self.text = ""

        self.on_change = None  # callback(text)
        self.on_enter = None   # callback(text)

        # Save previous button handlers so we can restore them on ENTER
        self._prev_click = button_input.on_click
        self._prev_double = button_input.on_double_click
        self._prev_long = button_input.on_long_click

        self.active = True

        self._init_handlers()

        self._refresh()

    # ---- Input event handlers ----

    def _on_click(self):
        if not self.active:
            return
        # Next character; wrap to next row at end of current row
        row_str = self.rows[self.row]
        self.col += 1
        if self.col >= len(row_str):
            self.row = (self.row + 1) % len(self.rows)
            self.col = 0
        self._refresh()

    def _on_double_click(self):
        if not self.active:
            return
        # Move down one row, keep column if possible
        self.row = (self.row + 1) % len(self.rows)
        row_str = self.rows[self.row]
        if self.col >= len(row_str):
            self.col = len(row_str) - 1
        if self.row == 0:
            self.col = 0
        self._refresh()

    def _on_long_click(self):
        if not self.active:
            return

        ch = self.rows[self.row][self.col]

        if ch == "+":  # ENTER
            if self.on_enter:
                self.on_enter(self.text)
            self._restore_handlers()
            # After ENTER we usually stop using the keyboard
            self.active = False
            self.text = ""

        elif ch == "-":  # backspace
            if self.text:
                self.text = self.text[:-1]
                if self.on_change:
                    self.on_change(self.text)

        else:
            # Normal character input
            if len(self.text) < self.max_len:
                self.text += ch
                if self.on_change:
                    self.on_change(self.text)
        self.row=0
        self.col=0
        self._refresh()

    def _init_handlers(self):
        # Hook into the Input callbacks
        self.input.on_click = self._on_click
        self.input.on_double_click = self._on_double_click
        self.input.on_long_click = self._on_long_click

    def _restore_handlers(self):
        """Restore the Input handlers to what they were before the keyboard."""
        self.input.on_click = self._prev_click
        self.input.on_double_click = self._prev_double
        self.input.on_long_click = self._prev_long

    # ---- Drawing ----

    def _refresh(self):
        if not self.display or not getattr(self.display, "driver", None):
            return
        if not self.active:
            return

        d = self.display
        d.fill(0)

        # Top line: current text (last 14 chars)
        show_text = self.text[-14:]
        d.small_text(show_text, 0, 0)

        # Four rows of characters
        for r, row_str in enumerate(self.rows):
            y = 8 + r * 8
            d.small_text(row_str, 0, y)
            if r == self.row:
                # underline current character (5px per char)
                ux = self.col * 5
                d.hline(ux, y + 7, 5, 1)

        d.show()

    # ---- Utility ----

    def reset(self, text=""):
        """Reset the keyboard text and position, stay active."""
        self.text = text[:self.max_len]
        self.row = 0
        self.col = 0
        self.active = True
        self._init_handlers()
        self._refresh()


# ---------------------------------------------------------------------------
# Input — single-button with click/double/long; uses Timer(0)
# ---------------------------------------------------------------------------
class Input:
    def __init__(self, pin_no=9, active_low=True, debounce_ms=80, long_ms=500, double_ms=500):
        self.debounce_ms = debounce_ms
        self.long_ms = long_ms
        self.double_ms = double_ms

        self._pin = Pin(pin_no, Pin.IN, Pin.PULL_UP if active_low else Pin.PULL_DOWN)
        self._press_level = 0 if active_low else 1

        self._last_irq = 0
        self._pressed = False
        self._down_ms = 0
        self._click_pending = False
        self._timer = None  # Timer(0) allocated on first use

        self.on_click = None
        self.on_double_click = None
        self.on_long_click = None

        trig = Pin.IRQ_FALLING | Pin.IRQ_RISING
        self._pin.irq(trigger=trig, handler=self._irq)

    def _irq(self, pin):
        now = time.ticks_ms()
        val = self._pin.value()
        if val == self._press_level:  # press
            if time.ticks_diff(now, self._last_irq) < self.debounce_ms:
                return
            self._last_irq = now
            self._pressed = True
            self._down_ms = now
            if self._click_pending:
                self._cancel_timer()
                self._click_pending = False
                self._pressed = False
                self._schedule(self._fire, 'double')
        else:  # release
            if not self._pressed:
                return
            self._pressed = False
            dur = time.ticks_diff(now, self._down_ms)
            if dur >= self.long_ms:
                self._cancel_timer()
                self._click_pending = False
                self._schedule(self._fire, 'long')
            else:
                self._click_pending = True
                self._start_timer()

    def _start_timer(self):
        t = self._timer
        if t is None:
            t = Timer(0)  # only 0 and 1 exist; BLE uses 1
            self._timer = t
        def _timeout(_t):
            if self._click_pending:
                self._click_pending = False
                self._schedule(self._fire, 'click')
        t.init(mode=Timer.ONE_SHOT, period=self.double_ms, callback=_timeout)

    def _cancel_timer(self):
        t = self._timer
        if t is not None:
            try: t.deinit()
            except: pass

    def _schedule(self, fn, arg):
        if _SCHEDULE:
            _SCHEDULE(fn, arg)
        else:
            fn(arg)

    def _fire(self, kind):
        if kind == 'click' and self.on_click: self.on_click()
        elif kind == 'double' and self.on_double_click: self.on_double_click()
        elif kind == 'long' and self.on_long_click: self.on_long_click()

# ---------------------------------------------------------------------------
# Bluetooth — simple advertiser/scanner for index + text messages
# - BLE imported lazily in __init__
# - Singleton controller
# - No scan/adv overlap
# - Uses Timer(1)
# ---------------------------------------------------------------------------

_ble_singleton = None  # global singleton BLE controller


def _short_id():
    # Use unique_id() instead of Wi-Fi MAC so we don't need network here
    return unique_id()[-1]


class Bluetooth:
    _ADV_TYPE_FLAGS        = 0x01
    _ADV_TYPE_NAME         = 0x09
    _ADV_TYPE_MANUFACTURER = 0xFF

    MAGIC      = b"GBSG"
    COMPANY_ID = b"\xFF\xFF"   # private use

    # BLE timing constants (µs), and adv interval
    SCAN_INTERVAL_US = 30000   # 30 ms
    SCAN_WINDOW_US   = 30000   # 30 ms (<= interval)
    SCAN_ACTIVE      = True
    ADV_INTERVAL_US  = 20000   # 20 ms

    # Events:
    #  1 = presence (no payload or idx=0)
    #  2 = index-based message (idx 0–255)
    #  3 = text-based message (short ASCII string)
    EVT_PRESENCE = 1
    EVT_INDEX    = 2
    EVT_TEXT     = 3

    def __init__(self, name="SM", adv_ms=300):
        import gc
        gc.collect()
        time.sleep_ms(50)

        # Lazy import of BLE stack (bluetooth / ubluetooth)
        try:
            import bluetooth as _btmod
            BLE = _btmod.BLE
        except:
            from ubluetooth import BLE  # fallback

        self.name = name
        self._name_bytes = name.encode()
        self.adv_ms = adv_ms
        self.dev_id = _short_id()

        # Callbacks:
        # - on_index(idx: int)
        # - on_text(text: str)
        # - on_message(payload)  # legacy (index OR text)
        self.on_index = None
        self.on_text = None
        self.on_message = None

        self._timer = Timer(1)  # distinct from Input's Timer(0)

        # Track last RX to drop duplicates (dev, ev, payload_key, ts)
        self._last_rx = (None, None, None, 0)

        global _ble_singleton
        if _ble_singleton is None:
            _ble_singleton = BLE()
        self.ble = _ble_singleton

        if not self.ble.active():
            self.ble.active(True)
        self.ble.irq(self._irq)

        # Optional debug ring (kept tiny if used)
        self._log = []

    # -------------------------------------------------------------------
    # Advertising / scanning helpers
    # -------------------------------------------------------------------
    def start_scan(self):
        # Restart scan with sane µs params + active scan
        try:
            self.ble.gap_scan(None)
        except:
            pass
        self.ble.gap_scan(0, self.SCAN_INTERVAL_US, self.SCAN_WINDOW_US, self.SCAN_ACTIVE)

    def _adv_struct(self, atype, data):
        return bytes((len(data) + 1, atype)) + data

    def _adv_payload(self, mfg_payload_full):
        """
        Build full ADV payload (Flags + optional Name + Manufacturer data).
        mfg_payload_full must already be: COMPANY_ID + MAGIC + payload...
        """
        flags = self._adv_struct(self._ADV_TYPE_FLAGS, b"\x06")
        name  = self._adv_struct(self._ADV_TYPE_NAME, self._name_bytes)
        mf    = self._adv_struct(self._ADV_TYPE_MANUFACTURER, mfg_payload_full)

        head = flags
        remain = 31 - len(head)

        # Try to include name if everything fits
        if len(name) + len(mf) <= remain:
            return head + name + mf

        # Drop name if needed; keep manufacturer intact
        if len(mf) <= remain:
            return head + mf

        # Last resort: truncate manufacturer (keep MAGIC if possible)
        return (head + mf)[:31]

    # -------------------------------------------------------------------
    # Manufacturer payload builders
    # -------------------------------------------------------------------
    def _mfg_index(self, dev_id, idx):
        # COMPANY_ID + MAGIC + dev + event + idx
        return self.COMPANY_ID + self.MAGIC + bytes((
            dev_id & 0xFF,
            self.EVT_INDEX,
            idx & 0xFF
        ))

    def _mfg_presence(self, dev_id):
        # Presence: idx=0 (unused)
        return self.COMPANY_ID + self.MAGIC + bytes((
            dev_id & 0xFF,
            self.EVT_PRESENCE,
            0
        ))

    def _mfg_text(self, dev_id, text):
        """
        Text payload:
          COMPANY_ID (2)
          MAGIC      (4)
          dev_id     (1)
          event      (1) = EVT_TEXT
          strlen     (1)
          text_bytes (strlen)
        """
        b = text.encode("ascii")[:20]  # keep it small for 31-byte ADV limit
        ln = len(b)
        return self.COMPANY_ID + self.MAGIC + bytes((
            dev_id & 0xFF,
            self.EVT_TEXT,
            ln & 0xFF
        )) + b

    # -------------------------------------------------------------------
    # Public API: presence, index, text
    # -------------------------------------------------------------------
    def presence(self):
        """
        Broadcast a presence message (no extra payload).
        """
        self._burst(self._mfg_presence(self.dev_id))

    def send_index(self, idx):
        """
        Broadcast a small integer index (0–255).
        """
        self._burst(self._mfg_index(self.dev_id, idx))

    def send_text(self, text):
        """
        Broadcast a short ASCII text message.
        Text is truncated to ~20 chars to fit into a single ADV packet.
        """
        self._burst(self._mfg_text(self.dev_id, text))

    # -------------------------------------------------------------------
    # Low-level burst / stop / resume scan
    # -------------------------------------------------------------------
    def _burst(self, mfg):
        payload = self._adv_payload(mfg)
        try:
            self.ble.gap_scan(None)
        except:
            pass

        self.ble.gap_advertise(self.ADV_INTERVAL_US, adv_data=payload)
        self._timer.init(
            mode=Timer.ONE_SHOT,
            period=self.adv_ms,
            callback=self._stop_adv_resume
        )

    def _stop_adv_resume(self, _t=None):
        try:
            self.ble.gap_advertise(None)
        finally:
            # Resume scanning with sane µs params + active scan
            try:
                self.ble.gap_scan(0, self.SCAN_INTERVAL_US, self.SCAN_WINDOW_US, self.SCAN_ACTIVE)
            except:
                pass

    # -------------------------------------------------------------------
    # RX path: IRQ handler + manufacturer parser
    # -------------------------------------------------------------------
    def _irq(self, event, data):
        # 5: _IRQ_SCAN_RESULT -> (addr_type, addr, adv_type, rssi, adv_data)
        if event == 5 and data:
            try:
                adv = data[4]
                dev, ev, payload = self._parse_mfg(memoryview(adv))
                if dev is None:
                    return

                # Dedup: drop repeats within 600ms for same (dev, ev, payload_key)
                now = time.ticks_ms()
                key = payload
                if isinstance(key, str):
                    key = ("T", key)   # distinguish string vs int
                elif isinstance(key, int):
                    key = ("I", key)

                last_dev, last_ev, last_key, last_ts = self._last_rx
                if (dev, ev, key) == (last_dev, last_ev, last_key):
                    if time.ticks_diff(now, last_ts) < 600:
                        return  # duplicate
                self._last_rx = (dev, ev, key, now)

                # Dispatch to callbacks
                if ev == self.EVT_INDEX and payload is not None:
                    idx = payload
                    # Prefer on_index; fall back to legacy on_message
                    cb = self.on_index or self.on_message
                    if cb:
                        if _SCHEDULE:
                            _SCHEDULE(lambda a: cb(a), idx)
                        else:
                            cb(idx)

                elif ev == self.EVT_TEXT and payload is not None:
                    text = payload
                    cb = self.on_text or self.on_message
                    if cb:
                        if _SCHEDULE:
                            _SCHEDULE(lambda a: cb(a), text)
                        else:
                            cb(text)

                elif ev == self.EVT_PRESENCE:
                    # You could add on_presence here if you want in future
                    pass

            except Exception as e:
                try:
                    self._log.append(("err", e))
                    if len(self._log) > 16:
                        self._log.pop(0)
                except:
                    pass

    def _parse_mfg(self, adv):
        """
        Extract our manufacturer payload from raw advertisement bytes.

        Returns:
            (dev, ev, payload)
        where:
            ev == EVT_INDEX  -> payload is int idx
            ev == EVT_TEXT   -> payload is str text
            ev == EVT_PRESENCE -> payload is None
        or (None, None, None) if not found.
        """
        i = 0
        n = len(adv)

        while i < n:
            ln = adv[i]
            if ln == 0 or i + 1 + ln > n:
                break

            t = adv[i + 1]
            if t == self._ADV_TYPE_MANUFACTURER:
                start = i + 2  # start of manufacturer data (no type/len)
                # Minimum: COMPANY_ID(2) + MAGIC(4) + dev(1) + ev(1) + one extra (idx/len)
                base_need = len(self.COMPANY_ID) + len(self.MAGIC) + 3
                if ln >= 1 + base_need:  # ln includes type(1)+data
                    if adv[start:start+2] == self.COMPANY_ID and adv[start+2:start+6] == self.MAGIC:
                        dev = adv[start+6]
                        ev  = adv[start+7]
                        third = adv[start+8]

                        if ev == self.EVT_INDEX:
                            idx = third
                            return dev, ev, idx

                        elif ev == self.EVT_TEXT:
                            strlen = third
                            # Data bytes for this field go up to i+1+ln
                            text_start = start + 9  # 2+4+1+1+1 = 9 bytes header
                            text_end   = text_start + strlen
                            if text_end <= i + 1 + ln:
                                text = bytes(adv[text_start:text_end]).decode("ascii")
                                return dev, ev, text
                            # If malformed, just ignore

                        elif ev == self.EVT_PRESENCE:
                            return dev, ev, None

            i += 1 + ln

        return None, None, None

class Robot:
    """
    Differential-drive robot using two continuous servos.

    - left_servo, right_servo: Servo instances
    - speed: base movement speed (0–1)
    - calibrate: offset applied to right-left difference to go straight
      +ve = right wheel too fast → slow right
      -ve = left wheel too fast → slow left
    """
    def __init__(self, left_servo, right_servo, speed=1, calibrate=0, display=None):
        self.display=display
        self.left_servo = left_servo
        self.right_servo = right_servo
        self.speed = speed
        self.cal = calibrate 

    def _apply_calibration(self, sp):
        """
        Calibration reduces the speed of the faster wheel.
        """
        left_sp  = max(min(sp - self.cal, 1), -1)
        right_sp = max(min(sp + self.cal, 1), -1)
        return left_sp, right_sp

    def go(self, left, right, duration):
        self.left_servo.speed(left)
        self.right_servo.speed(right)
        if duration:
            time.sleep(duration)
            self.stop()

    def forward(self, duration=1, speed=None):
        if self.display:
            self.display.small_text_center('Forwards', show=True, reset=True)
        sp = self.speed if speed is None else speed
        l, r = self._apply_calibration(sp)
        self.go(+l, -r, duration)

    def backward(self, duration=1, speed=None, reset=True):
        if self.display:
            self.display.small_text_center('Backwards', show=True, reset=True)
        sp = self.speed if speed is None else speed
        l, r = self._apply_calibration(sp)
        self.go(-l, +r, duration)

    def left(self, duration=1, speed=None):
        if self.display:
            self.display.small_text_center('Left', show=True, reset=True)
        sp = self.speed if speed is None else speed
        self.go(-sp, -sp, duration)

    def right(self, duration=1, speed=None):
        if self.display:
            self.display.small_text_center('Right', show=True, reset=True)
        sp = self.speed if speed is None else speed
        self.go(+sp, +sp, duration)

    def stop(self):
        if self.display:
            self.display.small_text_center('Stopped', show=True, reset=True)
        self.left_servo.stop()
        self.right_servo.stop()


class Servo:
    """
    Simple servo helper for MicroPython (ESP32, etc.)

    - Positional servo (e.g. SG90):
        s = SimpleServo(pin=18)
        s.angle(0)
        s.angle(90)
        s.angle(180)

    - Continuous rotation (e.g. FS90R):
        s = SimpleServo(pin=18, stop_us=1500)
        s.speed(0)   # stop
        s.speed(1)   # full forward
        s.speed(-1)  # full reverse
    """

    def __init__(self, pin, *, freq=50, min_us=500, max_us=2500, stop_us=None):
        _ensure_pwm()
        self.pwm = _pwm(Pin(pin), freq=freq)
        self.freq = freq
        self.min_us = min_us
        self.max_us = max_us
        self.stop_us = stop_us if stop_us is not None else (min_us + max_us) // 2

    def _us_to_duty(self, us):
        period_us = 1_000_000 // self.freq
        duty = int(us * 65535 // period_us)
        if duty < 0:
            duty = 0
        elif duty > 65535:
            duty = 65535
        return duty

    # ----- Positional servo -----
    def angle(self, degrees):
        if degrees < 0:
            degrees = 0
        elif degrees > 180:
            degrees = 180
        us = self.min_us + (self.max_us - self.min_us) * degrees // 180
        self.pwm.duty_u16(self._us_to_duty(us))

    def center(self):
        self.angle(90)

    # ----- Continuous servo -----
    def speed(self, value):
        if value > 1:
            value = 1
        elif value < -1:
            value = -1

        if value == 0:
            us = self.stop_us
        elif value > 0:
            us = self.stop_us + int((self.max_us - self.stop_us) * value)
        else:
            us = self.stop_us + int((self.stop_us - self.min_us) * value)

        self.pwm.duty_u16(self._us_to_duty(us))

    def stop(self):
        self.pwm.duty_u16(self._us_to_duty(self.stop_us))

    def deinit(self):
        self.pwm.deinit()

# ---------------------------------------------------------------------------
# Wi-Fi helper (lazy import; minimal)
# ---------------------------------------------------------------------------
def connect_wifi(ssid="scouts", password="greatbarton", timeout=10):
    network = _ensure_network()
    ntptime = _ensure_ntptime()
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to", ssid, "…")
        wlan.connect(ssid, password)
        for _ in range(timeout * 10):
            if wlan.isconnected():
                break
            time.sleep(0.1)
    if wlan.isconnected():
        try:
            ntptime.settime()
        except Exception:
            pass 
        print("Connected! IP:", wlan.ifconfig()[0])
        return wlan
    print("Failed to connect."); 
    return None
