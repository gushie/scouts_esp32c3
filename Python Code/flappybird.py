# flappybird.py — Flappy Bird for ESP32-C3 + 72x40 SH1106 window
# Needs: simple_esp.py
#
# One button controls everything:
#   - Short press: flap (make the bird go up)
#   - While on title screen: first press starts the game
#   - While on GAME OVER screen: press to restart (after a short delay)
#   - Long press: full reset back to title

from simple_esp import SmallDisplay, Input, Registry
from machine import Pin
import time

# ---------------------------------------------------------
# SCREEN AND BIRD SETTINGS
# ---------------------------------------------------------
SCREEN_WIDTH  = 72
SCREEN_HEIGHT = 40

BIRD_X = 18              # x-position of the bird on screen
BIRD_SIZE = 3            # the bird is a 3x3 pixel square

# How the bird moves up/down
GRAVITY = 0.28           # how fast the bird falls
FLAP_IMPULSE = -2.7      # how strong a flap is (negative = up)
MAX_VEL = 3.5            # maximum falling speed

# ---------------------------------------------------------
# PIPE AND MOVEMENT SETTINGS
# ---------------------------------------------------------
PIPE_SPACING = 40        # space between pipes (left/right)
SPEED = 1                # how many pixels pipes move left each frame

FPS = 60
FRAME_MS = int(1000 / FPS)

# ---------------------------------------------------------
# DIFFICULTY SETTINGS
# Start easier: narrow pipes + big gaps
# End harder: wider pipes + smaller gaps
# ---------------------------------------------------------
GAP_EASY    = 24         # gap size at the start of the game
GAP_HARD    = 10         # gap size when the game is hardest
PIPE_W_EASY = 2          # pipe width at the start
PIPE_W_HARD = 7          # pipe width when hardest

# Make sure the game never becomes impossible
MIN_GAP     = 8
MAX_GAP     = 24
MIN_PIPE_W  = 2
MAX_PIPE_W  = 8

# How many pipes it takes to go from easy → hard
MAX_DIFFICULTY_PIPES = 80

# Keep the gap away from the very top/bottom of the screen
GAP_MARGIN = 4

# ---------------------------------------------------------
# GAME STATE
# ---------------------------------------------------------
disp = SmallDisplay()
registry = Registry()
# Button on pin 9. We will use:
#   - on_press      for flapping / restarting
#   - on_long_click for full reset
btn = Input(pin_no=9, active_low=True, debounce_ms=20, long_ms=600, double_ms=400)

state = "title"          # can be: "title", "play", "dead"
score = 0
best = 0

bird_y = SCREEN_HEIGHT // 2   # start in the middle of the screen
vel = 0.0                     # bird's up/down speed

# Each pipe is a dictionary:
# {
#   "x": x-position,
#   "gap_y": middle of the gap,
#   "gap_height": height of the gap,
#   "width": how thick the pipe is,
#   "scored": True/False if we've already counted a point for this pipe
# }
pipes = []
pipe_count = 0           # how many pipes have been created in this run

# Used so GAME OVER screen doesn't vanish instantly
death_ms = 0
DEATH_COOLDOWN_MS = 1000  # wait 1 second before allowing restart
_rng = 1  # internal random number state

# ---------------------------------------------------------
# DETERMINISTIC RANDOM NUMBER GENERATOR
# (So the level is the same every time you play)
# ---------------------------------------------------------

def seed_rng(value=1):
    """Start the random number generator from a known seed value."""
    global _rng
    _rng = value & 0x7fffffff

def rand_range(n):
    """
    Return a "random" number from 0 to n-1.
    It is deterministic: same seed -> same sequence.
    """
    global _rng
    _rng = (_rng * 1103515245 + 12345) & 0x7fffffff
    return _rng % n if n > 0 else 0
# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def clamp(value, min_value, max_value):
    """Keep value between min_value and max_value."""
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value

def get_pipe_difficulty(pipe_index):
    """
    For pipe number 0,1,2,... decide:
      - gap_height (how big the gap is)
      - pipe_width (how thick the pipe is)

    The more pipes you pass, the harder the game gets:
      - gap becomes smaller
      - pipe width becomes larger
    """
    if MAX_DIFFICULTY_PIPES <= 1:
        progress = 1.0
    else:
        progress = pipe_index / (MAX_DIFFICULTY_PIPES - 1)
        if progress > 1.0:
            progress = 1.0

    # Mix between easy and hard values
    gap_height = int(GAP_EASY    + (GAP_HARD    - GAP_EASY)    * progress)
    pipe_width = int(PIPE_W_EASY + (PIPE_W_HARD - PIPE_W_EASY) * progress)

    # Make sure gap and width stay in safe ranges
    gap_height = clamp(gap_height, MIN_GAP, MAX_GAP)
    pipe_width = clamp(pipe_width, MIN_PIPE_W, MAX_PIPE_W)

    # Make sure the gap physically fits on the screen
    max_gap = SCREEN_HEIGHT - 2 * GAP_MARGIN
    if gap_height > max_gap:
        gap_height = max_gap

    return gap_height, pipe_width

def choose_gap_center_y(gap_height):
    """
    Choose where vertically the gap should be.
    We keep the gap away from the very top/bottom,
    and use our deterministic random numbers.
    """
    usable_space = SCREEN_HEIGHT - gap_height - 2 * GAP_MARGIN
    if usable_space <= 0:
        # If something goes wrong, just put the gap in the middle
        return SCREEN_HEIGHT // 2

    offset = rand_range(usable_space)
    gap_top = GAP_MARGIN + offset

    # Return the centre of the gap
    return gap_top + gap_height // 2

def spawn_pipe(start_x=None):
    """
    Create a new pipe and add it to the pipes list.
    Pipes are always to the right of the screen, then they move left.
    """
    global pipe_count

    if pipes:
        # If we already have pipes, put this one after the last one
        x = pipes[-1]["x"] + PIPE_SPACING if start_x is None else start_x
    else:
        # First pipe starts just off the right side of the screen
        x = start_x if start_x is not None else (SCREEN_WIDTH + 10)

    gap_height, pipe_width = get_pipe_difficulty(pipe_count)
    gap_center_y = choose_gap_center_y(gap_height)

    pipes.append({
        "x": x,
        "gap_y": gap_center_y,
        "gap_height": gap_height,
        "width": pipe_width,
        "scored": False
    })

    pipe_count += 1

def reset_game():
    """
    Reset everything for a new run,
    but keep the 'best' (high score).
    """
    global score, bird_y, vel, pipes, state, pipe_count

    # Make the level the same every time
    seed_rng(1)

    score = 0
    bird_y = SCREEN_HEIGHT // 2
    vel = 0.0
    pipes = []
    pipe_count = 0

    # Create a few pipes ahead of the bird
    spawn_pipe(SCREEN_WIDTH + 20)
    spawn_pipe(pipes[-1]["x"] + PIPE_SPACING)
    spawn_pipe(pipes[-1]["x"] + PIPE_SPACING)

    state = "title"
    draw_title_screen()

# ---------------------------------------------------------
# DRAWING FUNCTIONS
# ---------------------------------------------------------
def draw_bird(x, y):
    """Draw a 3x3 square for the bird."""
    top = int(y) - BIRD_SIZE // 2
    disp.fill_rect(x - 1, top, 3, 3, 1)

def draw_pipes():
    """Draw all pipes from the pipes list."""
    for pipe in pipes:
        x = pipe["x"]
        gap_y = pipe["gap_y"]
        gap_height = pipe["gap_height"]
        width = pipe["width"]

        top_pipe_height = gap_y - gap_height // 2
        bottom_pipe_y = gap_y + gap_height // 2

        # Top pipe (from top of screen down to top of gap)
        if top_pipe_height > 0:
            disp.fill_rect(x, 0, width, top_pipe_height, 1)

        # Bottom pipe (from bottom of gap down to bottom of screen)
        if bottom_pipe_y < SCREEN_HEIGHT:
            disp.fill_rect(x, bottom_pipe_y, width, SCREEN_HEIGHT - bottom_pipe_y, 1)

def draw_score():
    """Draw the current score in the top-right corner."""
    s = str(score)
    x = max(0, SCREEN_WIDTH - len(s) * 6)  # font is ~6 pixels wide per letter
    disp.small_text(s, x, 0)

def draw_title_screen():
    """Show the title screen."""
    disp.fill(0)
    disp.small_text_center("FLAPPY", 4)
    disp.hline(0, 14, SCREEN_WIDTH, 1)
    disp.small_text_center("CLICK=FLY", 16)
    disp.small_text_center("LONG=RESET", 24)
    if best > 0:
        disp.small_text(f"BEST:{best}", 0, 32)
    disp.show()

def draw_game_over():
    """Show the GAME OVER screen."""
    disp.fill(0)
    disp.small_text_center("GAME OVER", 4)
    disp.small_text_center(f"SCORE {score}", 16)
    disp.small_text_center(f"BEST  {best}", 24)
    disp.small_text_center("CLICK=RETRY", 32)
    disp.show()

def draw_game():
    """Draw the game (pipes, bird, score) if we are not dead."""
    if state == "dead":
        # When dead, we keep showing the GAME OVER screen instead
        return
    disp.fill(0)
    draw_pipes()
    draw_bird(BIRD_X, bird_y)
    draw_score()
    disp.show()

# ---------------------------------------------------------
# COLLISION DETECTION
# ---------------------------------------------------------
def has_collided():
    """
    Check if the bird hits the floor, ceiling, or a pipe.
    Return True if there is a collision.
    """
    # Hit the top or bottom of the screen?
    if bird_y < 0 or bird_y >= SCREEN_HEIGHT:
        return True

    # Bird's bounding box (3x3 square)
    bx0 = BIRD_X - 1
    bx1 = BIRD_X + 1
    by0 = int(bird_y) - 1
    by1 = int(bird_y) + 1

    for pipe in pipes:
        px0 = pipe["x"]
        px1 = pipe["x"] + pipe["width"] - 1
        gap_y = pipe["gap_y"]
        gap_height = pipe["gap_height"]

        gap_top = gap_y - gap_height // 2
        gap_bottom = gap_y + gap_height // 2 - 1

        # Only check collision if bird is in front of the pipe
        if bx1 >= px0 and bx0 <= px1:
            # If the bird is above the gap or below the gap, it hits the pipe
            if by1 < gap_top or by0 > gap_bottom:
                return True

    return False

# ---------------------------------------------------------
# GAME UPDATE (ONE FRAME)
# ---------------------------------------------------------
def update_game():
    """Update physics, move pipes, handle scoring, and detect death."""
    global bird_y, vel, score, best, state, death_ms, registry

    # 1) Bird physics
    vel = clamp(vel + GRAVITY, -5, MAX_VEL)
    bird_y += vel

    # 2) Move all pipes left
    for pipe in pipes:
        pipe["x"] -= SPEED

    # 3) Remove pipes that are off the left side of the screen
    while pipes and pipes[0]["x"] + pipes[0]["width"] < 0:
        pipes.pop(0)

    # 4) Add new pipes on the right side when needed
    while pipes and pipes[-1]["x"] < SCREEN_WIDTH:
        spawn_pipe()

    # 5) Check if we pass pipes to increase score
    for pipe in pipes:
        if (not pipe["scored"]) and (pipe["x"] + pipe["width"] - 1) < BIRD_X:
            pipe["scored"] = True
            score += 1

    # 6) Check for collision
    if has_collided():
        state = "dead"
        if score > best:
            best = score
        registry.set("flappy.best", best)
        death_ms = time.ticks_ms()
        draw_game_over()
        return

# ---------------------------------------------------------
# BUTTON HANDLERS
# ---------------------------------------------------------
def handle_long_press(_=None):
    """Long press: full reset to title screen."""
    reset_game()

btn.on_long_click = handle_long_press

def handle_button_press(_=None):
    """
    This function runs when the button is pressed quickly.

    Behaviour:
      - If on title screen: start the game and flap.
      - If playing: just flap.
      - If on GAME OVER screen and cooldown is over: restart and flap.
    """
    global state, vel, death_ms

    # 1) If we are on GAME OVER screen, maybe restart
    if state == "dead":
        # Wait a short time so GAME OVER can be read
        if time.ticks_diff(time.ticks_ms(), death_ms) < DEATH_COOLDOWN_MS:
            return

        reset_game()
        state = "play"
        vel = FLAP_IMPULSE
        return

    # 2) If we are on the title screen, first press starts the game
    if state == "title":
        state = "play"

    # 3) Flap (go up)
    vel = FLAP_IMPULSE

# Use the new handler for instant response on button press
btn.on_press = handle_button_press

# ---------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------
def main():
    global best
    try:
        disp.hard_reset()
    except:
        # If hard_reset() is not supported, just ignore the error
        pass

    best = registry.get("flappy.best", 0)
    reset_game()
    last_frame_time = time.ticks_ms()

    while True:
        if state == "title":
            # Title screen is static; just wait a bit
            time.sleep_ms(50)

        elif state == "play":
            update_game()
            draw_game()

            # Keep the game running at a steady FPS
            now = time.ticks_ms()
            dt = time.ticks_diff(now, last_frame_time)
            if dt < FRAME_MS:
                time.sleep_ms(FRAME_MS - dt)
            last_frame_time = now

        elif state == "dead":
            # GAME OVER screen is already drawn; just wait for button
            time.sleep_ms(50)

# Only run main() if this file is the main program
if __name__ == "__main__":
    main()
