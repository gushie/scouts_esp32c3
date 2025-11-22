from machine import Pin
from simple_esp import SmallDisplay
import time

def main():
    LED_PIN = 8      
    BUTTON_PIN = 9   

    led = Pin(LED_PIN, Pin.OUT)
    button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
    disp = SmallDisplay()
    disp.fill(0)
    disp.small_text_center('Press R Button', 16)
    disp.small_text_center('For LED', 24)
    disp.show()
    print("Press the button to turn the LED on.")

    while True:
        if button.value() == 1:  # pressed
            led.on()
        else:                    # released
            led.off()
        time.sleep_ms(10)

if __name__ == "__main__":
    main()