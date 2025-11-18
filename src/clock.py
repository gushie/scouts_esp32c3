# analog_clock.py — Analogue clock for 72x40 OLED window
from machine import RTC
from simple_esp import SmallDisplay, connect_wifi
import time, math


oled = SmallDisplay()  # 72x40 window mapped for your panel
rtc  = RTC()


# ---- Clock layout (fits 72x40) ----
W, H = oled.width, oled.height          # 72 x 40
CX, CY = W // 2, H // 2                 # center ~ (36,20)
R_FACE = 18                             # outer radius
R_HOUR = 11
R_MIN  = 16
R_SEC  = 17

def ang_to_xy(cx, cy, r, ang):
    # ang radians, 0 at 12 o'clock
    x = cx + int(r * math.cos(ang - math.pi/2))
    y = cy + int(r * math.sin(ang - math.pi/2))
    return x, y

def draw_ticks():
    # Hour ticks (12 marks). Shorter for clarity.
    for h in range(12):
        a = (h / 12) * 2 * math.pi
        x0, y0 = ang_to_xy(CX, CY, R_FACE-2, a)
        x1, y1 = ang_to_xy(CX, CY, R_FACE,   a)
        oled.line(x0, y0, x1, y1, 1)

def draw_face():
    oled.ellipse(CX, CY, R_FACE, R_FACE, 1)
    draw_ticks()

def draw_hands(h, m, s):
    # Angles (radians)
    a_sec = (s / 60.0) * 2 * math.pi
    a_min = ((m + s/60.0) / 60.0) * 2 * math.pi
    a_hr  = ((h % 12 + m/60.0) / 12.0) * 2 * math.pi

    # Endpoints
    hx, hy = ang_to_xy(CX, CY, R_HOUR, a_hr)
    mx, my = ang_to_xy(CX, CY, R_MIN,  a_min)
    sx, sy = ang_to_xy(CX, CY, R_SEC,  a_sec)

    # Draw (hour thicker via small cap)
    oled.line(CX, CY, hx, hy, 1)
    oled.line(CX, CY, mx, my, 1)
    oled.line(CX, CY, sx, sy, 1)
    # center dot
    oled.fill_rect(CX-1, CY-1, 3, 3, 1)

def main():
#    wlan = connect_wifi()   
    last_drawn_sec = -1
    while True:
        # Get time from RTC
        y, mo, d, wd, hh, mm, ss, _ = rtc.datetime()

        # Only fully redraw when the second changes
        if ss != last_drawn_sec:
            oled.fill(0)
            draw_face()
            draw_hands(hh, mm, ss)
            oled.show()
            last_drawn_sec = ss

        time.sleep(0.05)



# try_ntp()   # uncomment if Wi-Fi is up and you want auto time sync
if __name__ == "__main__":
    main()   # runs only when *executing* test.py directly
