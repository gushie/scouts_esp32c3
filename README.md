
# Scouts Digital Maker project for esp32-c3 with Micropython
Python code for the ESP32-C3 with a tiny OLED screen, used for the Scouts Digital Maker badge.

## Introduction
At our Digital Maker Camp we ran several rotating activities: soldering & electronics, graphics, Scratch, Python programming, and building simple robots.

For the Python and robotics sessions we used small **ESP32-C3** microcontrollers with **0.42" SH1106 OLED displays**. These boards include:

- a programmable LED  
- a single programmable button  
- onboard Wi-Fi and Bluetooth  
- 16 usable GPIO pins  
- USB-C power & programming  

We purchased them very cheaply from AliExpress by searching for  
**[esp32 c3 oled](https://www.aliexpress.com/w/wholesale-esp32-c3-oled.html?spm=a2g0o.detail.search.0)** — often as low as **£2 each**.

---

## Programming the ESP32-C3

Programming is done using the **Thonny Python IDE**:  
👉 https://thonny.org/

### Install MicroPython
You need to flash MicroPython onto each ESP32-C3.

A step-by-step video tutorial is available here:  
https://youtu.be/RUzyNFudo4Y

Steps:
1. Install Thonny.  
2. Connect the ESP32-C3 to your PC using USB-C.  
3. In Thonny, click the interpreter selector in the bottom-right.  
4. Choose **Configure Interpreter…**  
5. Select **MicroPython (ESP32)**.  
6. Click **Install or Update MicroPython** and choose **ESP32-C3 – espressif variant**.

---

### Copying the files
Download this repository via the green **Code** button above this, and then → **Download ZIP** 

In Thonny:

1. Enable the **Files** panel from *View*.  
2. Browse to the `Python Code` folder (was src) and right‑click each `.py` file → **Upload to /**.  
3. Double‑click files on the device to edit them.  
4. To save changes back to your PC, right‑click → **Download to…**.

Running **main.py** (or **main_menu.py**) loads a simple on‑device menu that lets you choose programs to run.

Whenever the ESP32-C3 powers on, **main.py runs automatically**, so it can be used standalone:

- from a USB charger  
- from a USB powerbank  
  *(note: some powerbanks may turn off due to low power draw)*

If you don't want the menu to run each time, edit the main.py file and delete the contents.

After you've copied the files and rebooted the device, you may find you no longer see the device files in Thonny. To resolve this
1. Choose the Exit option on the device menu
2. Click the Stop button in Thonny

If still not seeing them, go to the bottom right of Thonny, click MicroPython (ESP32) and choose MicroPython (ESP32) from the menu.

See [APPS](APPS.md) for a brief summary of the apps.
---

## Start tweaking the programs!
The whole point of the camp is experimentation. 🛠️

Feel free to modify any of the `.py` files:

- change displayed text  
- draw graphics  
- adjust animations  
- add new menu entries  
- build robot behaviours  

Don’t worry about breaking anything — you can always redownload the files or reset to the originals.

---

## simple_esp.py
`simple_esp.py` contains helper functions for:

- the mini OLED display  
- the single button  
- Bluetooth  
- ASCII‑art rendering  
- servos  
- robot driving  
- Wi-Fi connection
- Saving information  

It is intended to hide the more complicated programming, to give easier to use functions for the Scouts to program with.

See [SIMPLE_ESP](SIMPLE_ESP.md) documentation.

See the Robot folder for a simple robot that can be built with continuous servos.
