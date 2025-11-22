from simple_esp import SmallDisplay, Input
import time
from machine import Pin

display = SmallDisplay()
inp = Input(9)
led = Pin(8, Pin.OUT)

smile = """
  ####
 #    # 
# #  # #
#      #
# #  # #
#  ##  #
 #    #
  ####  
"""

sad = """
  ####
 #    # 
# #  # #
#      #
#  ##  #
# #  # #
 #    #
  ####  
"""

neutral = """
  ####
 #    # 
# #  # #
#      #
# #### #
#      #
 #    #
  ####  
"""

blank = """
  ####
 #    # 
# #  # #
#      #
#      #
#      #
 #    #
  ####  
"""

smile_image = display.create_image(smile)
sad_image = display.create_image(sad)
neutral_image = display.create_image(neutral)
blank_image = display.create_image(blank)

happy = False

def show_neutral():
    global happy
    display.image(neutral_image)
    display.show()
    happy = False

def show_blank():
    global happy
    display.image(blank_image)
    display.show()
    happy = False

def toggle_image():
    global happy
    happy = not happy
    if happy:
        display.image(smile_image)
        led.value(0)
    else:
        display.image(sad_image)
        led.value(1)
    display.show()

def main():    # Wire up button events
    inp.on_click = toggle_image
    inp.on_long_click = show_neutral
    inp.on_double_click = show_blank

    # Start state
    show_neutral()
    led.value(0)

    # Idle loop (events do the work)
    while True:
        time.sleep(0.1)

if __name__ == "__main__":
    main()