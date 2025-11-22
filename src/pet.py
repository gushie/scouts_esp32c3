# tami_pet.py — simple Tamagotchi-style game using simple_esp
#
# Layout:
#   Top    : Age
#   Middle : Pet image (happy / ok / sad / dead) via create_image
#   Bottom : Current action text
#
# Controls (single button on pin 9):
#   Click      : next action
#   Long click : perform current action
#   Double     : show status (and revive if dead)
#
# Instructions:
#   Shown once at start; first click hides them and starts the game.

from simple_esp import SmallDisplay, Input
from machine import Pin
import time

# ---- Game constants ----
ACTIONS = ["FEED", "PLAY", "WASH"]
TICK_MS = 5000  # pet state update interval (5 seconds)

MAX_STAT = 10
HUNGER_RATE  = 3  # +1 hunger every 3 ticks
BORED_RATE   = 2  # +1 boredom every 2 ticks
DIRTY_RATE   = 4  # +1 dirty every 4 ticks

# ---- Hardware ----
display = SmallDisplay()
button = Input(9)
led = Pin(8, Pin.OUT)

# ---- Pet state ----
pet = {
    "hunger": 0,
    "boredom": 0,
    "dirty": 0,
    "age_ticks": 0,
    "alive": True,
}

current_action = 0
_last_tick_ms = time.ticks_ms()
show_help = True  # instructions showing at start

# ---- Pet face ASCII art (only spaces and #) ----

happy_face = """
### #### ###
#  #    #  #
# # #  # # #
# #      # #
  #  ##  #
  #  ##  #
  #      #
  # #  # #
  #  ##  #
   #    #
    ####         
"""

ok_face = """
### #### ###
#  #    #  #
# # #  # # #
# #      # #
  #  ##  #
  #  ##  #
  #      #
  #      #
  # #### #
   #    #
    ####         
"""

sad_face = """
### #### ###
#  #    #  #
# # #  # # #
# #      # #
  #  ##  #
  #  ##  #
  #      #
  #  ##  #
  # #  # #
   #    #
    ####         
"""

dead_face = """
################
#  #        #  #
# # # #  # # # #
# #  #    #  # #
  # # #  # # #
  #          #
  #          #
  #          #
  #          #
  #          #
   #        #
    ######## 

"""

# Pre-create images for each mood (target height 24 so we can fit text)
FACE_W = 72
FACE_H = 24

happy_img  = display.create_image(happy_face,  target_w=FACE_W, target_h=FACE_H, reusable=False)
ok_img     = display.create_image(ok_face,     target_w=FACE_W, target_h=FACE_H, reusable=False)
sad_img    = display.create_image(sad_face,    target_w=FACE_W, target_h=FACE_H, reusable=False)
dead_img   = display.create_image(dead_face,   target_w=FACE_W, target_h=FACE_H, reusable=False)


# ---- Helpers ----

def clamp_stat(x):
    if x < 0:
        return 0
    if x > MAX_STAT:
        return MAX_STAT
    return x

def reset_pet():
    pet["hunger"] = 0
    pet["boredom"] = 0
    pet["dirty"] = 0
    pet["age_ticks"] = 0
    pet["alive"] = True

def pet_mood():
    if not pet["alive"]:
        return "dead"
    worst = max(pet["hunger"], pet["boredom"], pet["dirty"])
    if worst < 4:
        return "happy"
    elif worst < 7:
        return "ok"
    else:
        return "sad"

def get_face_image():
    mood = pet_mood()
    if mood == "happy":
        return happy_img
    if mood == "ok":
        return ok_img
    if mood == "sad":
        return sad_img
    return dead_img

def draw_game_screen():
    """Draw main game screen: score, face, action."""
    display.fill(0)

    # Top line: score (age)
    score = pet["age_ticks"]
    display.small_text("Age {}".format(score), 0, 0)

    # Middle: face image (24px tall) at y=8
    face_fb = get_face_image()
    display.image(face_fb, 0, 8)

    # Bottom: current action
    if not pet["alive"]:
        display.small_text("Hold click", 0, 32)
    else:
        act = ACTIONS[current_action]
        display.small_text("Action: {}".format(act[:7]), 0, 32)

    display.show()

def show_help_screen():
    """Show brief instructions until first click."""
    display.fill(0)
    display.small_text("Tami Pet", 0, 0)
    display.small_text("Click  : Next", 0, 8)
    display.small_text("Double : Do", 0, 16)
    display.small_text("Hold   : Info", 0, 24)
    display.small_text("Click to start", 0, 32)
    display.show()


def show_status_popup():
    """Show status (age and stats)."""
    age = pet["age_ticks"]
    line1 = "Status {}".format(pet_mood())
    line2 = "Age {}".format(age)
    line3 = "Hunger {}".format(pet["hunger"])
    line4 = "Boredom {}".format(pet["boredom"])
    line5 = "Dirty {}".format(pet["dirty"])
    display.fill(0)
    display.small_text(line1[:14], 0, 0)
    display.small_text(line2[:14], 0, 8)
    display.small_text(line3[:14], 0, 16)
    display.small_text(line4[:14], 0, 24)
    display.small_text(line5[:14], 0, 32)
    display.show()
    time.sleep_ms(1500)
    draw_game_screen()


def tick_pet():
    """Periodic update of pet's stats."""
    if not pet["alive"]:
        return

    pet["age_ticks"] += 1
    t = pet["age_ticks"]

    if t % HUNGER_RATE == 0:
        pet["hunger"] = clamp_stat(pet["hunger"] + 1)
    if t % BORED_RATE == 0:
        pet["boredom"] = clamp_stat(pet["boredom"] + 1)
    if t % DIRTY_RATE == 0:
        pet["dirty"] = clamp_stat(pet["dirty"] + 1)

    # Death check
    if (pet["hunger"] >= MAX_STAT or
        pet["boredom"] >= MAX_STAT or
        pet["dirty"] >= MAX_STAT):
        pet["alive"] = False
        led.value(1)
        display.notify("Oh no!", ms=800)
        led.value(0)

    draw_game_screen()

# ---- Button handlers ----

def on_click():
    """Single click: if help showing, hide help; otherwise cycle action."""
    global current_action, show_help
    if show_help:
        show_help = False
        draw_game_screen()
        return

    current_action = (current_action + 1) % len(ACTIONS)
    draw_game_screen()

def on_double():
    """Double click: perform current action."""
    if show_help:
        # ignore long presses while help is shown
        return

    if not pet["alive"]:
        display.notify("Too late...", ms=800)
        draw_game_screen()
        return

    act = ACTIONS[current_action]

    if act == "FEED":
        pet["hunger"] = clamp_stat(pet["hunger"] - 3)
        msg = "Fed!"
    elif act == "PLAY":
        pet["boredom"] = clamp_stat(pet["boredom"] - 3)
        msg = "Played!"
    elif act == "WASH":
        pet["dirty"] = clamp_stat(pet["dirty"] - 3)
        msg = "Washed!"
    else:
        msg = act

    led.value(1)
    display.notify(msg[:14], ms=600)
    led.value(0)

    draw_game_screen()

def on_long():
    """Long click: show status, or revive if dead."""
    if show_help:
        # ignore double while help is showing
        return

    if not pet["alive"]:
        display.notify("New pet!", ms=800)
        reset_pet()
        draw_game_screen()
    else:
        show_status_popup()


# ---- Main ----

def main():
    global _last_tick_ms
    button.on_click = on_click
    button.on_long_click = on_long
    button.on_double_click = on_double

    # Show help once
    show_help_screen()

    _last_tick_ms = time.ticks_ms()

    while True:
        now = time.ticks_ms()
        if not show_help and time.ticks_diff(now, _last_tick_ms) >= TICK_MS:
            _last_tick_ms = now
            tick_pet()
        time.sleep_ms(50)


if __name__ == "__main__":
    main()
