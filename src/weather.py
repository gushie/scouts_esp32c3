# main.py — ESP32-C3 + SH1106 (72x40 window) + Open-Meteo
# Requires mini_display.py in the board filesystem.
#
# What it shows (12 chars per line max):
# <CITY>
# <TEMP>°C  <COND>
# W<wind>  C<wcode>

import time
import urequests as requests
import ujson
from simple_esp import SmallDisplay
import wifi

# Your location (Bury St Edmunds approx shown here — change if you like)
CITY = "BURY ST ED"
LAT  = 52.247
LON  = 0.718

# Refresh period (seconds)
REFRESH_SEC = 600

# Use HTTP (no TLS hassle on tiny boards)
OPEN_METEO_URL = (
    "http://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}&current_weather=true"
)

# ---------- WEATHER CODE SHORT TEXT ----------
# Open-Meteo WMO codes (very compressed, 12-char lines budget)
def wcode_text(code):
    # Common codes mapped to short labels
    if code == 0:   return "CLEAR"
    if code in (1, 2):  return "PART CLOUD"
    if code == 3:   return "CLOUDY"
    if code in (45, 48): return "FOG"
    if code in (51, 53, 55): return "DRIZZLE"
    if code in (61, 63, 65): return "RAIN"
    if code in (66, 67): return "ICE RAIN"
    if code in (71, 73, 75): return "SNOW"
    if code in (77,): return "LIGHT SNOW"
    if code in (80, 81, 82): return "SHOWERS"
    if code in (85, 86): return "SNOW SHOWERS"
    if code in (95,): return "THUNDERSTORM"
    if code in (96, 99): return "TSTORM+HAIL"
    return "COND " + str(code)

def wind_dir_text(deg):
    """Return 1–2 letter compass point (8-point compass)."""
    if deg is None:
        return "--"
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    ix = int((deg + 22.5) % 360 / 45)
    return dirs[ix]

# ---------- FETCH ----------
def fetch_weather(lat, lon):
    url = OPEN_METEO_URL.format(lat=lat, lon=lon)
    r = None
    try:
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception("HTTP " + str(r.status_code))
        data = r.json()
        cw = data.get("current_weather") or {}
        # Open-Meteo returns °C and km/h for current_weather
        temp_c = cw.get("temperature")
        wind_kmh = cw.get("windspeed")
        code = cw.get("weathercode")
        wind_dir = cw.get("winddirection")
        return (temp_c, wind_kmh, code, wind_dir)
    finally:
        try:
            if r: r.close()
        except:
            pass

# ---------- UI ----------
def show_weather(disp, city, temp, wind_kmh, code, wind_dir):
    disp.fill(0)
    # Line 1: City (max 12 chars)
    disp.small_text(city, 0, 0)

    # Line 2: condition (try to keep under 12)
    line2 = wcode_text(code)
    disp.small_text(line2, 0, 8)

    # Line 3: temp
    line3 = "{}^C".format(temp)
    disp.small_text(line3, 0, 16)
    
    # Line 4: wind
    line4 = "{}km/h {}".format(wind_kmh, wind_dir_text(wind_dir)) 
    disp.small_text(line4, 0, 24)

    # Optional dividing line
    disp.hline(0, 32, 72, 1)

    disp.show()

def show_status(disp, text):
    disp.fill(0)
    disp.small_text(text[:16], 0, 16)
    disp.show()

# ---------- MAIN ----------
def main():
    d = SmallDisplay()
    try:
        d.hard_reset()
    except:
        pass

    show_status(d, "JOINING WIFI")
    ok = wifi.run_connect_saved()
    if not ok:
        show_status(d, "WIFI FAILED")
        return

    show_status(d, "GET WEATHER")

    t, wind, code, wind_dir = fetch_weather(LAT, LON)
    show_weather(d, CITY, t, wind, code, wind_dir)

if __name__ == "__main__":
    main()
