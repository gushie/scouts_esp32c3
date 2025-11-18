# main.py — Flappy Bird for ESP32-C3 + 72x40 SH1106 window
# Needs: mini_display.py (your version with SmallDisplay and Input)
from simple_esp import SmallDisplay, Input
from machine import Pin
import time
import urandom as random

# ----- GAME CONSTANTS -----
W = 72
H = 40
BIRD_X = 18
BIRD_SIZE = 3                 # 3x3 pixel "bird"
GRAVITY = 0.28
FLAP_IMPULSE = -2.7
MAX_VEL = 3.5

PIPE_W = 4
GAP = 15                      # gap height
PIPE_SPACING = 40             # distance between pipes
SPEED = 1                     # pixels/frame

FPS = 30
FRAME_MS = int(1000 / FPS)

# ----- STATE -----
disp = SmallDisplay()
btn = Input(pin_no=9, active_low=True, debounce_ms=80, long_ms=600, double_ms=400)

state = "title"               # "title", "play", "dead"
score = 0
best = 0

bird_y = H // 2
vel = 0.0
pipes = []                    # list of dicts: {"x": int, "gap_y": int, "scored": bool}

# ----- UTIL -----
def clamp(v, lo, hi): 
    return lo if v < lo else (hi if v > hi else v)

def new_gap_y():
    # Keep gap away from very top/bottom for fairness
    margin = 4
    return random.getrandbits(8) % (H - GAP - 2*margin) + margin + GAP//2

def spawn_pipe(x_start=None):
    x = x_start if x_start is not None else (pipes[-1]["x"] + PIPE_SPACING if pipes else W + 10)
    pipes.append({"x": x, "gap_y": new_gap_y(), "scored": False})

def reset_game():
    global score, bird_y, vel, pipes, state
    score = 0
    bird_y = H // 2
    vel = 0.0
    pipes = []
    # Spawn a few ahead
    spawn_pipe(W + 20)
    spawn_pipe(pipes[-1]["x"] + PIPE_SPACING)
    spawn_pipe(pipes[-1]["x"] + PIPE_SPACING)
    state = "title"
    draw_title()

# ----- INPUT CALLBACKS -----
def on_click():
    global state, vel
    if state == "title":
        state = "play"
    # flap
    vel = FLAP_IMPULSE

def on_long():
    reset_game()

btn.on_click = on_click
btn.on_long_click = on_long

# ----- DRAW -----
def draw_bird(x, y):
    # simple 3x3 filled square centered on y
    top = int(y) - BIRD_SIZE//2
    disp.fill_rect(x - 1, top, 3, 3, 1)

def draw_pipes():
    for p in pipes:
        x = p["x"]
        gy = p["gap_y"]
        top_h = gy - GAP//2
        bot_y = gy + GAP//2
        # top pipe
        if top_h > 0:
            disp.fill_rect(x, 0, PIPE_W, top_h, 1)
        # bottom pipe
        if bot_y < H:
            disp.fill_rect(x, bot_y, PIPE_W, H - bot_y, 1)

def draw_hud():
    s = str(score)
    # right align score
    x = max(0, W - len(s)*6)
    disp.small_text(s, x, 0)

def draw_title():
    disp.fill(0)
    disp.small_text_center("FLAPPY", 4)
    disp.hline(0, 14, W, 1)
    disp.small_text_center("CLICK=FLY", 18)
    disp.small_text_center("LONG=RESET", 26)
    if best > 0:
        disp.small_text(f"BEST:{best}", 0, 32)
    disp.show()

def draw_dead():
    disp.fill(0)
    disp.small_text_center("GAME OVER", 6)
    disp.small_text_center(f"SCORE {score}", 18)
    disp.small_text_center(f"BEST  {best}", 26)
    disp.small_text_center("CLICK=RETRY", 32)
    disp.show()

def render():
    disp.fill(0)
    draw_pipes()
    draw_bird(BIRD_X, bird_y)
    draw_hud()
    disp.show()

# ----- COLLISION -----
def collided():
    # top/bottom
    if bird_y < 0 or bird_y >= H:
        return True
    # pipes
    bx0 = BIRD_X - 1
    bx1 = BIRD_X + 1
    by0 = int(bird_y) - 1
    by1 = int(bird_y) + 1

    for p in pipes:
        px0 = p["x"]
        px1 = p["x"] + PIPE_W - 1
        gy  = p["gap_y"]
        gap0 = gy - GAP//2
        gap1 = gy + GAP//2 - 1

        # Only consider if overlapping horizontally
        if bx1 >= px0 and bx0 <= px1:
            # collides if bird's box intersects pipe solids (outside gap)
            if by1 < gap0 or by0 > gap1:
                return True
    return False

# ----- UPDATE -----
def update():
    global bird_y, vel, score, best, state

    # physics
    vel = clamp(vel + GRAVITY, -5, MAX_VEL)
    bird_y += vel

    # move pipes
    for p in pipes:
        p["x"] -= SPEED

    # remove offscreen, add new
    while pipes and pipes[0]["x"] + PIPE_W < 0:
        pipes.pop(0)
    while pipes and pipes[-1]["x"] < W:
        spawn_pipe()

    # score: when pipe right edge passes the bird x and not already scored
    for p in pipes:
        if not p["scored"] and (p["x"] + PIPE_W - 1) < BIRD_X:
            p["scored"] = True
            score += 1

    # collision
    if collided():
        state = "dead"
        if score > best:
            best = score
        draw_dead()

# ----- MAIN LOOP -----
def main():
    try:
        disp.hard_reset()
    except:
        pass

    reset_game()
    last = time.ticks_ms()

    while True:
        if state == "title":
            # idle animation: bob the bird a little
            # (lightweight bob without changing vel)
            # redraw every ~200ms to twinkle the underline
            time.sleep_ms(50)

        elif state == "play":
            update()
            render()
            # frame pacing
            now = time.ticks_ms()
            dt = time.ticks_diff(now, last)
            if dt < FRAME_MS:
                time.sleep_ms(FRAME_MS - dt)
            last = now

        elif state == "dead":
            # wait for click (handled in IRQ -> on_click)
            time.sleep_ms(50)
            # If user clicked, on_click sets state to "play" only when in title.
            # For "dead", treat a click as "retry":
            # We detect by checking if velocity was just set to FLAP_IMPULSE
            # but simpler: restart on any click by watching a small flag
            # Easy hack: if bird_y moved up abruptly, but to keep simple:
            # Use a timer: after 200ms, if state still dead, keep waiting.
            pass

# Make "dead" to "retry" behavior explicit by overriding on_click when dead
def dead_click_override():
    global state, vel
    if state == "dead":
        reset_game()
        state = "play"
        vel = FLAP_IMPULSE
    else:
        on_click()

# Rebind click to wrapper that handles "dead"
btn.on_click = dead_click_override

if __name__ == "__main__":
    main()
