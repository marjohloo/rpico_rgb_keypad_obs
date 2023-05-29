# rpico_rgb_keypad_obs v1.0.1
#
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
# Green:
#   11 scene keys, only one scene can be active at a time
# Cyan, Blue:
#   2 general keys
# Red, Yellow, Magenta:
#   3 toggle keys different key combos are sent when toggling on or off, so map these to start/stop
#   hotkeys for start/stop streaming etc
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
#
# pimoroni:
#   https://github.com/pimoroni/pmk-circuitpython
#
# SOFTWARE
#
# Inspired by:
#   https://github.com/pimoroni/pmk-circuitpython/blob/main/examples/obs-studio-toggle-and-mutex.py

import math
from pmk import PMK, number_to_xy, hsv_to_rgb
# from pmk.platform.keybow2040 import Keybow2040 as Hardware        # for Keybow 2040
from pmk.platform.rgbkeypadbase import RGBKeypadBase as Hardware  # for Pico RGB Keypad Base

import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode

# When true keycodes are sent
KC_LIVE = True

# LED Hues
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

# Hue:
#   Set this for the pad color.
#
# Group:
#   Set this to group pads together to operate like radio buttons (good for
#   scene selection). You can have many separate groups of keys as set by the
#   string set for the group
#
# Keycodes On:
#   These are the keyboard codes to be sent for normal, grouped and toggle on
#   pads.
#
# Keycodes Off:
#   These are the keyboard codes to be sent for toggle off pads, setting this
#   makes a toggle button, good for start/stop streaming
#
# Note:
#   Pads configured as toggles will be removed from any groups
#
config = [
    {"hue": hue["magenta"], "group": "scene", "keycodes_on": [Keycode.F13],                  "keycodes_off": None                        }, # 0
    {"hue": hue["magenta"], "group": "scene", "keycodes_on": [Keycode.F14],                  "keycodes_off": None                        }, # 1
    {"hue": hue["magenta"], "group": "scene", "keycodes_on": [Keycode.F15],                  "keycodes_off": None                        }, # 2
    {"hue": hue["magenta"], "group": "scene", "keycodes_on": [Keycode.F16],                  "keycodes_off": None                        }, # 3
    {"hue": hue["magenta"], "group": "scene", "keycodes_on": [Keycode.F17],                  "keycodes_off": None                        }, # 4
    {"hue": hue["magenta"], "group": "scene", "keycodes_on": [Keycode.F18],                  "keycodes_off": None                        }, # 5
    {"hue": hue["magenta"], "group": "scene", "keycodes_on": [Keycode.F19],                  "keycodes_off": None                        }, # 6
    {"hue": hue["magenta"], "group": "scene", "keycodes_on": [Keycode.F20],                  "keycodes_off": None                        }, # 7
    {"hue": hue["magenta"], "group": "scene", "keycodes_on": [Keycode.F21],                  "keycodes_off": None                        }, # 8
    {"hue": hue["magenta"], "group": "scene", "keycodes_on": [Keycode.F22],                  "keycodes_off": None                        }, # 9
    {"hue": hue["magenta"], "group": "scene", "keycodes_on": [Keycode.F23],                  "keycodes_off": None                        }, # A
    {"hue": hue["magenta"], "group": "scene", "keycodes_on": [Keycode.F24],                  "keycodes_off": None                        }, # B
    {"hue": hue["cyan"]   , "group": None,    "keycodes_on": [Keycode.SHIFT,   Keycode.F13], "keycodes_off": [Keycode.SHIFT, Keycode.F13]}, # C
    {"hue": hue["cyan"]   , "group": None,    "keycodes_on": [Keycode.SHIFT,   Keycode.F14], "keycodes_off": [Keycode.SHIFT, Keycode.F14]}, # D
    {"hue": hue["green"]  , "group": None,    "keycodes_on": [Keycode.CONTROL, Keycode.F13], "keycodes_off": [Keycode.ALT,   Keycode.F13]}, # E
    {"hue": hue["red"]    , "group": None   , "keycodes_on": [Keycode.CONTROL, Keycode.F14], "keycodes_off": [Keycode.ALT,   Keycode.F14]}  # F
]

#config = [
#    {"hue": hue["yg"]     , "group": "scene", "keycodes_on": [Keycode.F13],                  "keycodes_off": None                      }, # 0
#    {"hue": hue["yellow"] , "group": "scene", "keycodes_on": [Keycode.F14],                  "keycodes_off": None                      }, # 1
#    {"hue": hue["yg"]     , "group": "scene", "keycodes_on": [Keycode.F15],                  "keycodes_off": None                      }, # 2
#    {"hue": hue["red"]    , "group": None   , "keycodes_on": [Keycode.CONTROL, Keycode.F13], "keycodes_off": [Keycode.ALT, Keycode.F13]}, # 3
#    {"hue": hue["gc"]     , "group": "scene", "keycodes_on": [Keycode.F16],                  "keycodes_off": None                      }, # 4
#    {"hue": hue["green"]  , "group": "scene", "keycodes_on": [Keycode.F17],                  "keycodes_off": None                      }, # 5
#    {"hue": hue["gc"]     , "group": "scene", "keycodes_on": [Keycode.F18],                  "keycodes_off": None                      }, # 6
#    {"hue": hue["rry"]    , "group": None   , "keycodes_on": [Keycode.CONTROL, Keycode.F14], "keycodes_off": [Keycode.ALT, Keycode.F14]}, # 7
#    {"hue": hue["cb"]     , "group": "scene", "keycodes_on": [Keycode.F19],                  "keycodes_off": None                      }, # 8
#    {"hue": hue["cyan"]   , "group": "scene", "keycodes_on": [Keycode.F20],                  "keycodes_off": None                      }, # 9
#    {"hue": hue["cb"]     , "group": "scene", "keycodes_on": [Keycode.F21],                  "keycodes_off": None                      }, # A
#    {"hue": hue["ry"]     , "group": None,    "keycodes_on": [Keycode.SHIFT, Keycode.F13]  , "keycodes_off": None                      }, # B
#    {"hue": hue["bm"]     , "group": "scene", "keycodes_on": [Keycode.F22],                  "keycodes_off": None                      }, # C
#    {"hue": hue["blue"]   , "group": "scene", "keycodes_on": [Keycode.F23],                  "keycodes_off": None                      }, # D
#    {"hue": hue["bm"]     , "group": "scene", "keycodes_on": [Keycode.F24],                  "keycodes_off": None                      }, # E
#    {"hue": hue["ryy"]    , "group": None   , "keycodes_on": [Keycode.CONTROL, Keycode.F16], "keycodes_off": [Keycode.ALT, Keycode.F16]}  # F
#]

# LED Values (brightness)
VAL_SPLIT = (1.0/32.0)
VAL_MIN   = (VAL_SPLIT *  0.0)
VAL_OFF   = (VAL_SPLIT *  2.0)
VAL_ON    = (VAL_SPLIT * 30.0)
VAL_MAX   = (VAL_SPLIT * 32.0)
VAL_STEP  = 0.01

# Set up the keyboard and layout
keyboard = Keyboard(usb_hid.devices)
layout = KeyboardLayoutUS(keyboard)

# Set up Keybow
keybow = PMK(Hardware())
keys = keybow.keys

# Add runtime data to config
for i in range(16):
    # Defaults
    # Mode is toggle
    config[i]["mode"] = None
    # Set LED value to max
    config[i]["val"] = VAL_MAX
    # Not down
    config[i]["down"] = False
    # Not on
    config[i]["on"] = False
    # This is a toggle pad ?
    if config[i]["keycodes_off"] != None and len(config[i]["keycodes_off"]) and len(config[i]["keycodes_on"]):
        # Mode is toggle
        config[i]["mode"] = "toggle"
        # Can't be in a group
        config[i]["group"] = None
    # This is a grouped pad ?
    if config[i]["group"] != None and len(config[i]["keycodes_on"]):
        # Mode is group
        config[i]["mode"] = "group"
    # This is a key pad ?
    if config[i]["mode"] == None and len(config[i]["keycodes_on"]):
        # Mode is key
        config[i]["mode"] = "key"
    # This key has not got a mode ?
    if config[i]["mode"] == None:
        # Set LED value to min (not lit)
        config[i]["val"] = VAL_MIN

# Presses a list of keycodes
def press_kcs(kcs):
    print(f'keycode press {kcs} {KC_LIVE}')
    if KC_LIVE:
        if len(kcs) == 1:
            keyboard.press(kcs[0])
        elif len(kcs) == 2:
            keyboard.press(kcs[0], kcs[1])
        elif len(kcs) == 3:
            keyboard.press(kcs[0], kcs[1], kcs[2])

# Releases a list of keycodes
def release_kcs(kcs):
    print(f'keycode release {kcs} {KC_LIVE}')
    if KC_LIVE:
        if len(kcs) == 1:
            keyboard.release(kcs[0])
        elif len(kcs) == 2:
            keyboard.release(kcs[0], kcs[1])
        elif len(kcs) == 3:
            keyboard.release(kcs[0], kcs[1], kcs[2])

# Process key presses/releases
for key in keys:
    # Pad pressed?
    @keybow.on_press(key)
    def press_handler(key):
        print(f'keypad press {key.number}')
        # Pad is now down
        config[key.number]["down"] = True
        # Normal pad ?
        if config[key.number]["mode"] == "key":
            # Press the on keycodes
            press_kcs(config[key.number]["keycodes_on"])
        # Toggle pad ?
        elif config[key.number]["mode"] == "toggle":
            # Toggle is currently on ?
            if config[key.number]["on"]:
                # Turn off
                config[key.number]["on"] = False
                # Press the off keycodes
                press_kcs(config[key.number]["keycodes_off"])
            # Toggle is currently off ?
            else:
                # Turn on
                config[key.number]["on"] = True
                # Press the on keycodes
                press_kcs(config[key.number]["keycodes_on"])
        # Grouped pad ?
        elif config[key.number]["mode"] == "group":
            # Turn on the pressed pad
            config[key.number]["on"] = True
            # Press the on keycodes
            press_kcs(config[key.number]["keycodes_on"])
            # Loop through pads
            for i in range(16):
                # Not the pad that has just been pressed ?
                if i != key.number:
                    # This pad is in the same group as the pad that has just been pressed ?
                    if config[i]["mode"] == "group" and config[i]["group"] == config[key.number]["group"]:
                        # The pad is on ?
                        if config[i]["on"]:
                            # Turn it off
                            config[i]["on"] = False
                            # Set val to minimum
                            config[i]["val"] = VAL_MIN

    # Pad released ?
    @keybow.on_release(key)
    def release_handler(key):
        print(f'keypad release {key.number}')
        # Pad is not down
        config[key.number]["down"] = False
        # Normal pad ?
        if config[key.number]["mode"] == "key":
            # Release on keycodes
            release_kcs(config[key.number]["keycodes_on"])
        # Toggle pad ?
        elif config[key.number]["mode"] == "toggle":
            # Pad has been toggled on ?
            if config[key.number]["on"]:
                # Release on keycodes
                release_kcs(config[key.number]["keycodes_on"])
            # Pad has just been turned off ?
            else:
                # Release off keycodes
                release_kcs(config[key.number]["keycodes_off"])
        # Grouped pad
        elif config[key.number]["mode"] == "group":
            # Release on keycodes
            release_kcs(config[key.number]["keycodes_on"])

    # Pad held ?
    @keybow.on_hold(key)
    def hold_handler(key):
        pass

# Main loop
while True:
    # Always remember to call keybow.update() on every iteration of your loop!
    keybow.update()
    # Loop through pads
    for i in range(16):
        # Start with LED off
        h = 0.0
        s = 0.0
        v = 0.0
        # No mode ?
        if config[i]["mode"] == None:
            # Turn off LED
            keys[i].set_led(0, 0, 0)
        # Pad has a mode ?
        else:
            # Pad is down ?
            if config[i]["down"]:
                # Normal or grouped pad
                if config[i]["mode"] == "key" or config[i]["mode"] == "group":
                    # Go to full brightness
                    config[i]["val"] = v = VAL_MAX
                # Toggle pad?
                elif config[i]["mode"] == "toggle":
                    # Toggled on ?
                    if config[i]["on"]:
                        # Go to full brightness
                        config[i]["val"] = v = VAL_MAX
                    # Toggled off ?
                    else:
                        # Go to min brightness
                        config[i]["val"] = v = VAL_MIN
            # Pad is not down
            else:
                # Pad is on
                if config[i]["on"]:
                    # Set target on brightness
                    v = VAL_ON
                # Pad is off ?
                else:
                    # Set target off brightness
                    v = VAL_OFF
            # Target value above current value ?
            if v > config[i]["val"]:
                # Move towards target
                if v - config[i]["val"] > VAL_STEP:
                    config[i]["val"] += VAL_STEP
                else:
                    config[i]["val"] = v
            # Target value below current value
            elif v < config[i]["val"]:
                # Move towards target
                if config[i]["val"] - v > VAL_STEP:
                    config[i]["val"] -= VAL_STEP
                else:
                    config[i]["val"] = v
            # Pad has a hue ?
            if config[i]["hue"] is not None:
                # Set full saturation
                s = 1.0
                # Set hue
                h = config[i]["hue"]
            # Convert the hue to RGB values.
            r, g, b = hsv_to_rgb(h, s, config[i]["val"])
 #           if i == 0:
 #                print(f'{h} {s} {config[i]["val"]} {r} {g} {b} rgb')
            # Finally set the LED
            keys[i].set_led(r, g, b)
