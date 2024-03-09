# License : GPLv2.0
# copyright (c) 2023  Dave Bailey
# Author: Dave Bailey (dbisu, @daveisu)


import time
import digitalio
from digitalio import DigitalInOut, Pull
from adafruit_debouncer import Debouncer
import board
from board import *
import pwmio
import asyncio
import usb_hid
from adafruit_hid.keyboard import Keyboard

# comment out these lines for non_US keyboards
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS as KeyboardLayout
from adafruit_hid.keycode import Keycode

# uncomment these lines for non_US keyboards
# replace LANG with appropriate language
#from keyboard_layout_win_LANG import KeyboardLayout
#from keycode_win_LANG import Keycode

duckyCommands = {
    'WINDOWS': Keycode.WINDOWS, 'GUI': Keycode.GUI,
    'APP': Keycode.APPLICATION, 'MENU': Keycode.APPLICATION, 'SHIFT': Keycode.SHIFT,
    'ALT': Keycode.ALT, 'CONTROL': Keycode.CONTROL, 'CTRL': Keycode.CONTROL,
    'DOWNARROW': Keycode.DOWN_ARROW, 'DOWN': Keycode.DOWN_ARROW, 'LEFTARROW': Keycode.LEFT_ARROW,
    'LEFT': Keycode.LEFT_ARROW, 'RIGHTARROW': Keycode.RIGHT_ARROW, 'RIGHT': Keycode.RIGHT_ARROW,
    'UPARROW': Keycode.UP_ARROW, 'UP': Keycode.UP_ARROW, 'BREAK': Keycode.PAUSE,
    'PAUSE': Keycode.PAUSE, 'CAPSLOCK': Keycode.CAPS_LOCK, 'DELETE': Keycode.DELETE,
    'END': Keycode.END, 'ESC': Keycode.ESCAPE, 'ESCAPE': Keycode.ESCAPE, 'HOME': Keycode.HOME,
    'INSERT': Keycode.INSERT, 'NUMLOCK': Keycode.KEYPAD_NUMLOCK, 'PAGEUP': Keycode.PAGE_UP,
    'PAGEDOWN': Keycode.PAGE_DOWN, 'PRINTSCREEN': Keycode.PRINT_SCREEN, 'ENTER': Keycode.ENTER,
    'SCROLLLOCK': Keycode.SCROLL_LOCK, 'SPACE': Keycode.SPACE, 'TAB': Keycode.TAB,
    'BACKSPACE': Keycode.BACKSPACE,
    'A': Keycode.A, 'B': Keycode.B, 'C': Keycode.C, 'D': Keycode.D, 'E': Keycode.E,
    'F': Keycode.F, 'G': Keycode.G, 'H': Keycode.H, 'I': Keycode.I, 'J': Keycode.J,
    'K': Keycode.K, 'L': Keycode.L, 'M': Keycode.M, 'N': Keycode.N, 'O': Keycode.O,
    'P': Keycode.P, 'Q': Keycode.Q, 'R': Keycode.R, 'S': Keycode.S, 'T': Keycode.T,
    'U': Keycode.U, 'V': Keycode.V, 'W': Keycode.W, 'X': Keycode.X, 'Y': Keycode.Y,
    'Z': Keycode.Z, 'F1': Keycode.F1, 'F2': Keycode.F2, 'F3': Keycode.F3,
    'F4': Keycode.F4, 'F5': Keycode.F5, 'F6': Keycode.F6, 'F7': Keycode.F7,
    'F8': Keycode.F8, 'F9': Keycode.F9, 'F10': Keycode.F10, 'F11': Keycode.F11,
    'F12': Keycode.F12,

}
def convertLine(line):
    return [
        duckyCommands.get(key.upper(), 
                          getattr(Keycode, 
                                  key.upper(), 
                                  None)) 
                                  for key in filter(
                                      None, 
                                      line.split(" ")
                                      )
                                      ]
def runScriptLine(line):
    for k in line:
        kbd.press(k)
    kbd.release_all()

def sendString(line):
    layout.write(line)

def parseLine(line):
    global defaultDelay
    commands = {
        "#": lambda line: None,
        "Delay": lambda line: time.sleep(float(line[6:])/1000),
        "String": lambda line: sendString(line[7:]),
        "Print": lambda line: print("[Script]: " + line[6:]),
        "Import": lambda line: runScript(line[7:]),
        "Default_Delay": lambda line: setattr(defaultDelay, int(line[14:]) * 10),
        "Defaultdelay": lambda line: setattr(defaultDelay, int(line[13:]) * 10),
        "Led": lambda line: setattr(led, not led.value)
    }
    
    for command, action in commands.items():
        if line.startswith(command):
            action(line)
            return

    newScriptLine = convertLine(line)
    runScriptLine(newScriptLine)
# Initialize keyboard and layout
kbd = Keyboard(usb_hid.devices)
layout = KeyboardLayout(kbd)

# Initialize button
button1_pin = DigitalInOut(GP22)
button1_pin.switch_to_input(pull=Pull.UP)
button1 = Debouncer(button1_pin)

# Initialize payload selection switches
payload_pins = [GP4, GP5, GP10, GP11]
payload_files = ["payload.txt", "payload2.txt", "payload3.txt", "payload4.txt"]

payload_pin_states = [not DigitalInOut(pin).value for pin in payload_pins]
selected_payload_index = payload_pin_states.index(True) if True in payload_pin_states else 0

def getProgrammingStatus():
    # check GP0 for setup mode
    progStatusPin = digitalio.DigitalInOut(GP0)
    progStatusPin.switch_to_input(pull=digitalio.Pull.UP)
    progStatus = not progStatusPin.value
    return progStatus

defaultDelay = 0

def runScript(file):
    global defaultDelay
    duckyScriptPath = file
    try:
        with open(duckyScriptPath, "r", encoding='utf-8') as f:
            previousLine = ""
            for line in f:
                line = line.rstrip()
                if line.startswith("REPEAT"):
                    for _ in range(int(line[7:])):
                        parseLine(previousLine)
                        time.sleep(defaultDelay / 1000)
                else:
                    parseLine(line)
                    previousLine = line
                time.sleep(defaultDelay / 1000)
    except OSError as e:
        print("Unable to open file ", file)

def selectPayload():
    return payload_files[selected_payload_index]

async def blink_led(led):
    print("Blink")
    if(board.board_id == 'raspberry_pi_pico'):
        blink_pico_led(led)

async def blink_pico_led(led):
    """
    This function blinks the LED connected to the Raspberry Pi Pico.
    """
    print("Starting blink_pico_led")
    while True:
        for i in range(100):
            # PWM LED up and down
            led.duty_cycle = int(i * 2 * 65535 / 100) if i < 50 else 65535 - int((i - 50) * 2 * 65535 / 100)
            await asyncio.sleep(0.01)
        await asyncio.sleep(0)
async def monitor_buttons(button1):
    """
    This function monitors button presses and releases.
    """
    print("Starting monitor_buttons")
    button1_down = False
    while True:
        button1.update()

        button1_pushed = button1.fell
        button1_released = button1.rose

        if button1_pushed:
            print("Button 1 pushed")
            button1_down = True

        if button1_released:
            print("Button 1 released")
            if button1_down:
                print("Push and released")
                # Run selected payload
                payload = selectPayload()
                print("Running", payload)
                runScript(payload)
                print("Done")
            button1_down = False

        await asyncio.sleep(0)
