# scouts_esp32c3
Python code for the esp32c3 with tiny oled screen for the Scouts Digital Maker badge

## Introduction
We held a Digital Maker Camp, where we had various activities on rotation, such as soldering/electronics, graphics, scratch, python programming and building robots.
For the python programming and robots we made use of little esp32-c3 microcontrollers with tiny 0.42 OLED screens. The esp32-c3 microcontrollers include one LED and button that we have programmatic access to, as well as onboard wifi and bluetooth support, and 16 pins we can connect to other components.

We bought the microcontrollers from Aliexpress, searching for [esp32 c3 oled](https://www.aliexpress.com/w/wholesale-esp32-c3-oled.html?spm=a2g0o.detail.search.0) - we were able to purchase them for as little as £2 each. 

## Programming
To program the microcontrollers, we connect them to laptops via USB-C, and use the [Thonny Python IDE](https://thonny.org/)

### Install Micropython
We first need to install Micropython onto the esp32-c3. See this video for details: https://youtu.be/RUzyNFudo4Y
Install Thonny. Connect the esp32-c3 to your PC via the USB port. Open Thonny. On the bottom right of Thonny click where it says Local Python and then click Configure Interpreter. Choose Micropython (ESP32). Click Install or Update Micropython. Here choose ESP32-C3, espressif variant. 

### Copy files
Download the files from this github page by clicking the green Code button and downloading the zip file.
In Thonny, enable the 'Files' option on the View menu. Here you can now copy files across by right clicking on the .py files in the src folder, and choosing to upload to /
You can then double click on the files on the Micropython device panel to edit them. It is a good idea if changing them to copy them back to the PC by right clicking and choosing the 'Download to...' option.

Running the main.py (or main_menu.py) will load a menu to select from the programs to run them. The main program automatically runs whenever the esp32 is powered up. It doesn't need to be connected to a PC, it can be plugged into a USB charger, or USB powerbank. (Unfortunately the device doesn't draw much power, so some powerbanks do have a habit of automatically turning off, thinking nothing is connected.)

### Start tweaking the programs
Feel free to edit the files to change what they do! Don't worry about breaking anything. You can always 'undo' or download the files and start over!

## Tutorial
See the "Scouts Micropython Mini‑course for esp32‑c3.docx" file to begin programming in Python

## simple_esp.py
Simple_ESP is a file full of functions to more easily access the features of the ESP32-C3 and the OLED screen. See [separate documentation](SIMPLE_ESP.md) for more information
