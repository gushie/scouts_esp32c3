# main.py — Sideways Tetris (left→right) for 72×40 OLED
# Needs: mini_display.py with SmallDisplay, Input
from simple_esp import SmallDisplay, Input
import time
import urandom as random

# ======= GRID / RENDER =======
CELL = 4
COLS = 18   # 18 * 4 = 72 px
ROWS = 10   # 10 * 4 = 40 px
W = COLS * CELL
H = ROWS * CELL

# ======= PIECES (Tetriminos) =======
# Each piece is a list of rotation states; each state is a list of (x,y) offsets.
# Pivot is (0,0). We'll position piece by integer grid coords (px, py).
TETROS = [
    # I
    [[(-1,0),(0,0),(1,0),(2,0)],
     [(0,-1),(0,0),(0,1),(0,2)]],
    # O
    [[(0,0),(1,0),(0,1),(1,1)]],
    # T
    [[(-1,0),(0,0),(1,0),(0,1)],
     [(0,-1),(0,0),(0,1),(1,0)],
     [(-1,0),(0,0),(1,0),(0,-1)],
     [(0,-1),(0,0),(0,1),(-1,0)]],
    # L
    [[(-1,0),(0,0),(1,0),(1,1)],
     [(0,-1),(0,0),(0,1),(1,-1)],
     [(-1,-1),(-1,0),(0,0),(1,0)],
     [(-1,1),(0,-1),(0,0),(0,1)]],
    # J
    [[(-1,0),(0,0),(1,0),(-1,1)],
     [(0,-1),(0,0),(0,1),(1,1)],
     [(-1,0),(0,0),(1,0),(1,-1)],
     [(-1,-1),(0,-1),(0,0),(0,1)]],
    # S
    [[(0,0),(1,0),(-1,1),(0,1)],
     [(0,-1),(0,0),(1,0),(1,1)]],
    # Z
    [[(-1,0),(0,0),(0,1),(1,1)],
     [(1,-1),(0,0),(1,0),(0,1)]],
]

# ======= GAME STATE =======
disp = SmallDisplay()
btn  = Input(pin_no=9, active_low=True, debounce_ms=80, long_ms=600, double_ms=350)

grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]  # 0 empty, 1 filled
score = 0
best  = 0
level = 0

piece = None
rot   = 0
px    = 0
py    = ROWS // 2
next_piece = None

state = "title"  # title, play, over

# ======= UTILS =======
def rnd(n): return random.getrandbits(16) % n

def new_piece():
    global piece, rot, px, py
    piece = next_piece if next_piece is not None else rnd(len(TETROS))
    rot   = 0
    px    = spawn_x_for(piece, rot)   # <<< was 0; now inside bounds
    py    = ROWS // 2 - 1
    py    = max(0, min(ROWS-2, py + (rnd(5)-2)//2))


def roll_next():
    global next_piece
    next_piece = rnd(len(TETROS))

def cells_of(p=None, r=None, ox=0, oy=0):
    """Yield absolute grid cells for the current (or given) piece/rotation."""
    if p is None:
        p = piece
    if r is None:
        r = rot
    shape = TETROS[p][r]
    for dx, dy in shape:
        yield px + dx + ox, py + dy + oy


def in_bounds(x, y):
    return 0 <= x < COLS and 0 <= y < ROWS

def can_place(ox=0, oy=0, r=None):
    rr = rot if r is None else r
    for x, y in cells_of(piece, rr, ox, oy):
        if not in_bounds(x, y) or grid[y][x]:
            return False
    return True

def lock_piece():
    for x, y in cells_of():
        if in_bounds(x,y):
            grid[y][x] = 1

def clear_full_columns():
    """Clear any column that is full (all rows filled). Return number cleared."""
    global grid
    full = []
    for c in range(COLS):
        if all(grid[r][c] for r in range(ROWS)):
            full.append(c)
    if not full:
        return 0
    # Build a new grid by skipping cleared cols and shifting left
    keep_cols = [c for c in range(COLS) if c not in set(full)]
    new_grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    # Copy kept columns to the left-most positions
    for new_c, c in enumerate(keep_cols):
        for r in range(ROWS):
            new_grid[r][new_c] = grid[r][c]
    grid = new_grid
    return len(full)

def add_score(cols_cleared):
    global score, level, best
    if cols_cleared == 0:
        return
    # Basic scoring: 40 * n^2
    score += 40 * (cols_cleared ** 2)
    if score > best:
        best = score
    # Increase level every 200 points
    level = min(10, score // 200)

def game_over():
    global state
    state = "over"

# ======= INPUT =======
def on_click():
    # rotate clockwise
    global rot
    if state != "play": 
        start_or_retry()
        return
    new_r = (rot + 1) % len(TETROS[piece])
    # Wallkick-lite: try up/down 1 cell if rotation collides
    if can_place(r=new_r): 
        rot = new_r
        return
    if can_place(oy=-1, r=new_r): 
        rot = new_r; move(0,-1); return
    if can_place(oy=1,  r=new_r): 
        rot = new_r; move(0,1);  return

def on_double():
    # nudge up
    if state != "play": 
        return
    move(0,-1)

def on_long():
    # nudge down
    if state != "play": 
        return
    move(0,1)

btn.on_click = on_click
btn.on_double_click = on_double
btn.on_long_click = on_long

# ======= MOVEMENT / STEP =======
def move(ox, oy):
    global px, py
    if can_place(ox, oy):
        px += ox
        py += oy
        return True
    return False

def step_forward():
    """Gravity to the RIGHT: try to move +x; if blocked, lock and spawn next."""
    global state
    if move(1, 0):
        return
    # Cannot move right: lock
    lock_piece()
    cleared = clear_full_columns()
    add_score(cleared)
    # New piece
    roll_next()
    new_piece()
    # If blocked immediately => game over
    if not can_place():
        game_over()

# ======= RENDER =======
def draw_cell(gx, gy, c=1):
    disp.fill_rect(gx*CELL, gy*CELL, CELL, CELL, c)

def draw_grid():
    # Filled cells
    for y in range(ROWS):
        for x in range(COLS):
            if grid[y][x]:
                draw_cell(x,y,1)
    # Active piece (draw last)
    for x, y in cells_of():
        if in_bounds(x,y):
            draw_cell(x,y,1)

def draw_hud():
    # Top bar: score (right), level (left)
    s = str(score)
    disp.small_text(f"L{level}", 0, 0)
    disp.small_text(s[:12], max(0, 72 - len(s)*6), 0)

def render_play():
    disp.fill(0)
    draw_grid()
    draw_hud()
    disp.show()

def draw_title():
    disp.fill(0)
    disp.small_text_center("SIDE TETRIS", 4)
    disp.hline(0, 14, 72, 1)
    disp.small_text_center("CLICK ROTATE", 18)
    disp.small_text_center("DBL UP  LNG DN", 26)
    disp.small_text(f"BEST:{best}", 0, 32)
    disp.show()

def draw_over():
    disp.fill(0)
    disp.small_text_center("GAME OVER", 6)
    disp.small_text_center(f"SCORE {score}", 18)
    disp.small_text_center(f"BEST  {best}", 26)
    disp.small_text_center("CLICK=RETRY", 32)
    disp.show()

# ======= FLOW =======
def start_or_retry():
    global grid, score, level, state, piece, next_piece
    if state == "title":
        if piece is None:
            next_piece = None
            roll_next()
            new_piece()
        state = "play"
    elif state == "over":
        grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        score = 0; level = 0
        next_piece = None
        roll_next()
        new_piece()
        state = "play"


def reset_game():
    global grid, score, level, state
    grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    score = 0
    level = 0
    roll_next()
    new_piece()
    state = "title"
    draw_title()

def min_dx_for(p_idx, r):
    return min(dx for dx, _ in TETROS[p_idx][r])

def spawn_x_for(p_idx, r):
    # place so leftmost block sits at x=0
    return -min_dx_for(p_idx, r)


# ======= MAIN LOOP =======
def main():
    try:
        disp.hard_reset()
    except:
        pass
    reset_game()

    # Base step interval (ms). Gets faster with level.
    base_ms = 520
    last_step = time.ticks_ms()
    last_anim = last_step

    while True:
        if state == "title":
            # simple blink underline
            now = time.ticks_ms()
            if time.ticks_diff(now, last_anim) > 400:
                last_anim = now
                draw_title()
            time.sleep_ms(20)

        elif state == "play":
            now = time.ticks_ms()
            # compute current step delay (speed up by ~40ms/level)
            step_ms = max(140, base_ms - level*40)
            if time.ticks_diff(now, last_step) >= step_ms:
                last_step = now
                step_forward()
                if state == "over":
                    draw_over()
                    continue
            render_play()
            time.sleep_ms(10)

        elif state == "over":
            # wait for click -> on_click will start_or_retry()
            time.sleep_ms(20)

if __name__ == "__main__":
    main()
