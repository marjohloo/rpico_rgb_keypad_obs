
# SPDX-FileCopyrightText: 2021 Philip Howard
#
# SPDX-License-Identifier: MIT

# This example gives you eight toggle and eight "mutex" key bindings for OBS studio
#
# MUTEX
# Use the top eight buttons (nearest the USB connector) to bind your scenes.
# The light on these is mutually exclusive- the one you last pressed should light up,
# and this is the scene you should be broadcasting.
#
# TOGGLE
# The bottom eight buttons will toggle on/off, emitting a slightly different keycode
# for each state. This means they will *always* indicate the toggle state.
# Bind these to Mute/Unmute audio by pressing the key once in Mute and once again in Unmute.
#
# Keep OBS focussed when using these... to avoid weirdness!

# Drop the `pmk` folder
# into your `lib` folder on your `CIRCUITPY` drive.

import math
from pmk import PMK, number_to_xy, hsv_to_rgb
# from pmk.platform.keybow2040 import Keybow2040 as Hardware          # for Keybow 2040
from pmk.platform.rgbkeypadbase import RGBKeypadBase as Hardware  # for Pico RGB Keypad Base

import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

# Test - when true keycodes are not sent
TEST = True

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
VAL_SPLIT = (1.0/16.0)
VAL_OFF   = (VAL_SPLIT *  1.0)
VAL_ON    = (VAL_SPLIT * 10.0)
VAL_DOWN  = (VAL_SPLIT * 16.0)
VAL_STEP  = 0.025

# Keycodes
KC_COMMON = Keycode.WINDOWS # Common - always sent
KC_ON     = Keycode.CONTROL # On - sent for normal presses and toggle on
KC_OFF    = Keycode.ALT     # Off - sent for toggle off'

# Configuration
config = [
    { "hue": hue["magenta"], "mode": MODE_KEY,  "kc": Keycode.KEYPAD_ZERO,          "down": False, "on": True,  "val": 0.0},
    { "hue": hue["magenta"], "mode": MODE_KEY,  "kc": Keycode.KEYPAD_ONE,           "down": False, "on": False, "val": 0.0},
    { "hue": hue["magenta"], "mode": MODE_KEY,  "kc": Keycode.KEYPAD_TWO,           "down": False, "on": False, "val": 0.0},
    { "hue": hue["magenta"], "mode": MODE_KEY,  "kc": Keycode.KEYPAD_THREE,         "down": False, "on": False, "val": 0.0},
    { "hue": hue["magenta"], "mode": MODE_KEY,  "kc": Keycode.KEYPAD_FOUR,          "down": False, "on": False, "val": 0.0},
    { "hue": hue["magenta"], "mode": MODE_KEY,  "kc": Keycode.KEYPAD_FIVE,          "down": False, "on": False, "val": 0.0},
    { "hue": hue["magenta"], "mode": MODE_KEY,  "kc": Keycode.KEYPAD_SIX,           "down": False, "on": False, "val": 0.0},
    { "hue": hue["magenta"], "mode": MODE_KEY,  "kc": Keycode.KEYPAD_SEVEN,         "down": False, "on": False, "val": 0.0},
    { "hue": hue["magenta"], "mode": MODE_KEY,  "kc": Keycode.KEYPAD_EIGHT,         "down": False, "on": False, "val": 0.0},
    { "hue": hue["magenta"], "mode": MODE_KEY,  "kc": Keycode.KEYPAD_NINE,          "down": False, "on": False, "val": 0.0},
    { "hue": hue["magenta"], "mode": MODE_KEY,  "kc": Keycode.KEYPAD_FORWARD_SLASH, "down": False, "on": False, "val": 0.0},
    { "hue": hue["magenta"], "mode": MODE_KEY,  "kc": Keycode.KEYPAD_ASTERISK,      "down": False, "on": False, "val": 0.0},
    { "hue": hue["magenta"], "mode": MODE_KEY,  "kc": Keycode.KEYPAD_MINUS,         "down": False, "on": False, "val": 0.0},
    { "hue": hue["magenta"], "mode": MODE_KEY,  "kc": Keycode.KEYPAD_PLUS,          "down": False, "on": False, "val": 0.0},
    { "hue": hue["magenta"], "mode": MODE_KEY,  "kc": Keycode.KEYPAD_ENTER,         "down": False, "on": False, "val": 0.0},
    { "hue": hue["magenta"], "mode": MODE_NONE, "kc": Keycode.KEYPAD_PERIOD,        "down": False, "on": False, "val": 0.0},
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
#        if False:
#            binding = keycodes[key.number]
#            if binding is None:
#                return
#            if type(binding) is tuple:
#                binding, _ = binding
#                states[key.number] = not states[key.number]
#                if states[key.number]:
#                    keyboard.press(Keycode.LEFT_CONTROL, Keycode.LEFT_SHIFT, binding)
#                else:
#                    keyboard.press(Keycode.LEFT_CONTROL, Keycode.LEFT_SHIFT, Keycode.LEFT_ALT, binding)
#            else:
#                keyboard.press(Keycode.LEFT_CONTROL, Keycode.LEFT_SHIFT, binding)
#                active = key.number

    @keybow.on_release(key)
    def release_handler(key):
        global active
        print("{} released".format(key.number))
        config[key.number]["down"] = False
 #       if False:
 #           binding = keycodes[key.number]
 #           if binding is None:
 #               return
 #           if type(binding) is tuple:
 #               binding, _ = binding
 #               if states[key.number]:
 #                   keyboard.release(Keycode.LEFT_CONTROL, Keycode.LEFT_SHIFT, binding)
 #               else:
 #                   keyboard.release(Keycode.LEFT_CONTROL, Keycode.LEFT_SHIFT, Keycode.LEFT_ALT, binding)
 #           else:
 #               keyboard.release(Keycode.LEFT_CONTROL, Keycode.LEFT_SHIFT, binding)

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
        if config[i]["mode"] == MODE_NONE:
            # Turn off key
            keys[i].set_led(0, 0, 0)
        else:
            # Pad is down ?
            if config[i]["down"]:
                # Set target val
                v = VAL_DOWN
                # Instant jump to down value
                config[i]["val"] = v
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
            if i == 0:
                # print(f'{h} {s} {config[i]["val"]} {r} {g} {b} rgb')
                pass
            # Display it on the key!
            keys[i].set_led(r, g, b)
