# SPDX-FileCopyrightText: 2023 Martin Looker
#
# SPDX-License-Identifier: MIT
#
# DESCRIPTION
#
# This code provides a controller for OBS studio acting as a USB keyboard
#
# Keys are as follows:
#
# Green: 11 scene keys, only one scene can be active at a time
# Cyan: 2 general keys
# Red, Yellow, Magenta: 3 toggle keys different key combos are sent when toggling on
# or off, so map these to start/stop hotkeys for start/stop streaming etc
#
# HARDWARE
#
# https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html
# https://shop.pimoroni.com/products/pico-rgb-keypad-base
#
# LIBRARIES
#
# adafruit:
#   https://circuitpython.org/board/raspberry_pi_pico/
#   https://github.com/adafruit/Adafruit_DotStar
#   https://github.com/adafruit/Adafruit_CircuitPython_HID
# pimoroni:
#   https://github.com/pimoroni/pmk-circuitpython
#
# SOFTWARE
#
# Inspired by:
#   https://github.com/pimoroni/pmk-circuitpython/blob/main/examples/obs-studio-toggle-and-mutex.py

import math
from pmk import PMK, number_to_xy, hsv_to_rgb
# from pmk.platform.keybow2040 import Keybow2040 as Hardware          # for Keybow 2040
from pmk.platform.rgbkeypadbase import RGBKeypadBase as Hardware  # for Pico RGB Keypad Base

import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

# When true keycodes are sent
KC_LIVE = True

# Modes
MODE_NONE   = 0
MODE_KEY    = 1
MODE_SCENE  = 2
MODE_TOGGLE = 3

# Hues
HUE_SPLIT = (1.0/24.0)
hue = {
    "red"     : (HUE_SPLIT *  0.0),
    "rry"     : (HUE_SPLIT *  1.0),
    "ry"      : (HUE_SPLIT *  2.0),
    "ryy"     : (HUE_SPLIT *  3.0),
    "yellow"  : (HUE_SPLIT *  4.0),
    "yyg"     : (HUE_SPLIT *  5.0),
    "yg"      : (HUE_SPLIT *  6.0),
    "ygg"     : (HUE_SPLIT *  7.0),
    "green"   : (HUE_SPLIT *  8.0),
    "ggc"     : (HUE_SPLIT *  9.0),
    "gc"      : (HUE_SPLIT * 10.0),
    "gcc"     : (HUE_SPLIT * 11.0),
    "cyan"    : (HUE_SPLIT * 12.0),
    "ccb"     : (HUE_SPLIT * 13.0),
    "cb"      : (HUE_SPLIT * 14.0),
    "cbb"     : (HUE_SPLIT * 15.0),
    "blue"    : (HUE_SPLIT * 16.0),
    "bbm"     : (HUE_SPLIT * 17.0),
    "bm"      : (HUE_SPLIT * 18.0),
    "bmm"     : (HUE_SPLIT * 19.0),
    "magenta" : (HUE_SPLIT * 20.0),
    "mmr"     : (HUE_SPLIT * 21.0),
    "mr"      : (HUE_SPLIT * 22.0),
    "mrr"     : (HUE_SPLIT * 23.0),
}

# Values
VAL_SPLIT = (1.0/32.0)
VAL_MIN   = (VAL_SPLIT *  0.0)
VAL_OFF   = (VAL_SPLIT *  1.0)
VAL_ON    = (VAL_SPLIT * 20.0)
VAL_MAX   = (VAL_SPLIT * 32.0)
VAL_STEP  = 0.01

# Keycodes
KC_COMMON = Keycode.WINDOWS # Common - always sent
KC_ON     = Keycode.CONTROL # On - sent for normal presses and toggle on
KC_OFF    = Keycode.ALT     # Off - sent for toggle off'

# Configuration
config = [
    { "hue": hue["green"],   "mode": MODE_SCENE,  "kc": Keycode.KEYPAD_ZERO,          "down": False, "on": False, "val": 1.0 }, # 0
    { "hue": hue["green"],   "mode": MODE_SCENE,  "kc": Keycode.KEYPAD_ONE,           "down": False, "on": False, "val": 1.0 }, # 1
    { "hue": hue["green"],   "mode": MODE_SCENE,  "kc": Keycode.KEYPAD_FOUR,          "down": False, "on": False, "val": 1.0 }, # 2
    { "hue": hue["green"],   "mode": MODE_SCENE,  "kc": Keycode.KEYPAD_SEVEN,         "down": False, "on": False, "val": 1.0 }, # 3
    { "hue": hue["green"],   "mode": MODE_SCENE,  "kc": Keycode.KEYPAD_PERIOD,        "down": False, "on": False, "val": 1.0 }, # 4
    { "hue": hue["green"],   "mode": MODE_SCENE,  "kc": Keycode.KEYPAD_TWO,           "down": False, "on": False, "val": 1.0 }, # 5
    { "hue": hue["green"],   "mode": MODE_SCENE,  "kc": Keycode.KEYPAD_FIVE,          "down": False, "on": False, "val": 1.0 }, # 6
    { "hue": hue["green"],   "mode": MODE_SCENE,  "kc": Keycode.KEYPAD_EIGHT,         "down": False, "on": False, "val": 1.0 }, # 7
    { "hue": hue["cyan"],    "mode": MODE_KEY,    "kc": Keycode.F12,                  "down": False, "on": False, "val": 1.0 }, # 8
    { "hue": hue["green"],   "mode": MODE_SCENE,  "kc": Keycode.KEYPAD_THREE,         "down": False, "on": False, "val": 1.0 }, # 9
    { "hue": hue["green"],   "mode": MODE_SCENE,  "kc": Keycode.KEYPAD_SIX,           "down": False, "on": False, "val": 1.0 }, # A
    { "hue": hue["green"],   "mode": MODE_SCENE,  "kc": Keycode.KEYPAD_NINE,          "down": False, "on": False, "val": 1.0 }, # B
    { "hue": hue["cyan"],    "mode": MODE_KEY,    "kc": Keycode.KEYPAD_ENTER,         "down": False, "on": False, "val": 1.0 }, # C
    { "hue": hue["magenta"], "mode": MODE_TOGGLE, "kc": Keycode.KEYPAD_PLUS,          "down": False, "on": False, "val": 1.0 }, # D
    { "hue": hue["yellow"],  "mode": MODE_TOGGLE, "kc": Keycode.KEYPAD_MINUS,         "down": False, "on": False, "val": 1.0 }, # E
    { "hue": hue["red"],     "mode": MODE_TOGGLE, "kc": Keycode.KEYPAD_PERIOD,        "down": False, "on": False, "val": 1.0 }, # F
]

# Set up the keyboard and layout
keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)

# Set up Keybow
keybow = PMK(Hardware())
keys = keybow.keys

#states = [False for _ in keys]

# Increment step to shift animation across keys.
step = 0
active = -1

for key in keys:
    @keybow.on_press(key)
    def press_handler(key):
        global active
        print("{} pressed".format(key.number))
        config[key.number]["down"] = True
        if config[key.number]["kc"] != None:
            if config[key.number]["mode"] == MODE_KEY:
                print(f'press {KC_COMMON}+{KC_ON}+{config[key.number]["kc"]}')
                if KC_LIVE: keyboard.press(KC_COMMON, KC_ON, config[key.number]["kc"])
            elif config[key.number]["mode"] == MODE_TOGGLE:
                if config[key.number]["on"]:
                    config[key.number]["on"] = False
                    print(f'press {KC_COMMON}+{KC_OFF}+{config[key.number]["kc"]}')
                    if KC_LIVE: keyboard.press(KC_COMMON, KC_OFF, config[key.number]["kc"])
                else:
                    config[key.number]["on"] = True
                    print(f'press {KC_COMMON}+{KC_ON}+{config[key.number]["kc"]}')
                    if KC_LIVE: keyboard.press(KC_COMMON, KC_ON, config[key.number]["kc"])
            elif config[key.number]["mode"] == MODE_SCENE:
                config[key.number]["on"] = True
                print(f'press {KC_COMMON}+{KC_ON}+{config[key.number]["kc"]}')
                if KC_LIVE: keyboard.press(KC_COMMON, KC_ON, config[key.number]["kc"])                    
                for i in range(16):
                    if i != key.number:
                        if config[i]["mode"] == MODE_SCENE:
                            if config[i]["on"]:
                                config[i]["on"] = False
                                config[i]["val"] = VAL_MIN

    @keybow.on_release(key)
    def release_handler(key):
        global active
        print("{} released".format(key.number))
        config[key.number]["down"] = False
        if config[key.number]["kc"] != None:
            if config[key.number]["mode"] == MODE_KEY:
                print(f'release {KC_COMMON}+{KC_ON}+{config[key.number]["kc"]}')
                if KC_LIVE: keyboard.release(KC_COMMON, KC_ON, config[key.number]["kc"])
            elif config[key.number]["mode"] == MODE_TOGGLE:
                if config[key.number]["on"]:
                    print(f'release {KC_COMMON}+{KC_ON}+{config[key.number]["kc"]}')
                    if KC_LIVE: keyboard.release(KC_COMMON, KC_ON, config[key.number]["kc"])
                else:
                    print(f'release {KC_COMMON}+{KC_OFF}+{config[key.number]["kc"]}')
                    if KC_LIVE: keyboard.release(KC_COMMON, KC_OFF, config[key.number]["kc"])
            elif config[key.number]["mode"] == MODE_SCENE:
                print(f'release {KC_COMMON}+{KC_ON}+{config[key.number]["kc"]}')
                if KC_LIVE: keyboard.release(KC_COMMON, KC_ON, config[key.number]["kc"])                     

    @keybow.on_hold(key)
    def hold_handler(key):
        pass


while True:
    # Always remember to call keybow.update() on every iteration of your loop!
    keybow.update()
    # Loop through keys
    for i in range(16):
        h = 0
        s = 0
        v = 0
        # No mode ?
        if config[i]["mode"] == MODE_NONE or config[i]["kc"] == None:
            # Turn off key
            keys[i].set_led(0, 0, 0)
        else:
            # Pad is down ?
            if config[i]["down"]:
                if config[i]["mode"] == MODE_KEY or config[i]["mode"] == MODE_SCENE:
                    config[i]["val"] = VAL_MAX
                    v = VAL_MAX
                elif config[i]["mode"] == MODE_TOGGLE:
                    if config[i]["on"]:
                        config[i]["val"] = v = VAL_MAX
                    else:
                        config[i]["val"] = v = VAL_MIN
            # Pad is not down
            else:
                if config[i]["on"]:
                    v = VAL_ON
                else:
                    v = VAL_OFF
            # Target value above current value ?
            if v > config[i]["val"]:
                if v - config[i]["val"] > VAL_STEP:
                    config[i]["val"] += VAL_STEP
                else:
                    config[i]["val"] = v
            elif v < config[i]["val"]:
                if config[i]["val"] - v > VAL_STEP:
                    config[i]["val"] -= VAL_STEP
                else:
                    config[i]["val"] = v
            # Pad has a hue ?
            if config[i]["hue"] is not None:
                s = 1.0
                h = config[i]["hue"]
            # Convert the hue to RGB values.
            r, g, b = hsv_to_rgb(h, s, config[i]["val"])
 #           if i == 0:
 #                print(f'{h} {s} {config[i]["val"]} {r} {g} {b} rgb')
            # Display it on the key!
            keys[i].set_led(r, g, b)
