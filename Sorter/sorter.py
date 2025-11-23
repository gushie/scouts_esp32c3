import network
import socket
import time
from simple_esp import Servo, connect_wifi

# ========= CONFIG =========

SERVO_PIN = 4          # change if your servo is on a different GPIO
IDLE_MIN_ANGLE = 80
IDLE_MAX_ANGLE = 100
IDLE_STEP_MS   = 5     # ms between wiggle steps
# ==========================

# Create positional servo (SG90 style)
servo = Servo(pin=SERVO_PIN)  # adjust min_us / max_us here if needed
servo.angle(60)  # initial neutral / parked


def create_server():
    addr = ("0.0.0.0", 80)
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print("Listening on", addr)
    return s

# ====== Servo motion patterns (equivalent to Arduino doCereal/doMallow) ======

def do_left():
    print("CMD: left (1)")
    servo.angle(0)
    time.sleep(2)

    for pos in range(0, 76):  # 0 to 75
        servo.angle(pos)
        time.sleep_ms(5)

    time.sleep(1)

def do_right():
    print("CMD: right (2)")
    servo.angle(180)
    time.sleep(2)

    for pos in range(180, 74, -1):  # 180 down to 75
        servo.angle(pos)
        time.sleep_ms(20)

    time.sleep(1)

def handle_command(cmd):
    if cmd == "1":
        do_left()
    elif cmd == "2":
        do_right()
    elif cmd == "stop":
        print("CMD: stop")
        servo.angle(90)   # neutral-ish
    else:
        print("Unknown command:", cmd)

# ====== HTTP helpers ======

def parse_path(request_line):
    # e.g. "GET /cmd?c=1 HTTP/1.1"
    try:
        parts = request_line.split()
        if len(parts) < 2:
            return "/"
        return parts[1]  # path + query
    except Exception:
        return "/"

def get_cmd_from_path(path):
    # Expect something like "/cmd?c=1"
    if not path.startswith("/cmd"):
        return None

    # Split off query string
    qmark = path.find("?")
    if qmark == -1:
        return None
    query = path[qmark+1:]  # after '?'

    # Simple query parser: look for "c="
    for pair in query.split("&"):
        if pair.startswith("c="):
            return pair[2:]
    return None

def send_response(client, body="OK", status="200 OK"):
    # Minimal HTTP response with CORS for browser fetch()
    try:
        client.send("HTTP/1.1 " + status + "\r\n")
        client.send("Content-Type: text/plain\r\n")
        client.send("Access-Control-Allow-Origin: *\r\n")
        client.send("Access-Control-Allow-Private-Network: true\r\n")
        client.send("Connection: close\r\n")
        client.send("\r\n")
        client.send(body)
    except OSError:
        pass

# ====== Main loop ======

def main():
    wlan = connect_wifi()
    ip = wlan.ifconfig()[0]
    print("Use this in your p5 code as ESP_URL:")
    print("  http://{}".format(ip))

    server = create_server()

    # Idle wiggle state
    idle_pos = IDLE_MIN_ANGLE
    idle_up = True
    last_idle_step = time.ticks_ms()

    while True:
        # Non-blocking accept with small timeout-ish behaviour
        server.settimeout(0.1)
        try:
            client, addr = server.accept()
        except OSError:
            client = None

        if client:
            print("Client connected from", addr)
            client.settimeout(2)

            try:
                request = client.recv(1024)
            except OSError:
                request = b""

            if not request:
                client.close()
                continue

            # First line only
            try:
                req_line = request.split(b"\r\n", 1)[0].decode()
            except UnicodeError:
                req_line = ""

            print("Request line:", req_line)
            path = parse_path(req_line)

            if path.startswith("/cmd"):
                cmd = get_cmd_from_path(path)
                if cmd is None:
                    send_response(client, "Missing c parameter", "400 Bad Request")
                else:
                    handle_command(cmd)
                    send_response(client, "Command {} executed".format(cmd))
            else:
                body = "Tiny Sorter ESP32-C3 (MicroPython)\nUse /cmd?c=1 or /cmd?c=2"
                send_response(client, body)

            client.close()
            print("Client disconnected")

        # Idle wiggle when nothing else happening
        now = time.ticks_ms()
        if time.ticks_diff(now, last_idle_step) >= IDLE_STEP_MS:
            if idle_up:
                idle_pos += 3
                if idle_pos >= IDLE_MAX_ANGLE:
                    idle_pos = IDLE_MAX_ANGLE
                    idle_up = False
            else:
                idle_pos -= 3
                if idle_pos <= IDLE_MIN_ANGLE:
                    idle_pos = IDLE_MIN_ANGLE
                    idle_up = True

            servo.angle(idle_pos)
            last_idle_step = now

# Run on boot
if __name__ == "__main__":
    main()
