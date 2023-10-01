#!/usr/bin/env python3
from gpiozero import Button
from signal import pause
import sounddevice as sd
import os
import wavio

# Make sure that the 'waves' folder exists, and if it does not, create it

path = os.path.expanduser('~') + '/waves'

isExist = os.path.exists(path)

if not isExist:
    os.makedirs(path)
    print("The new directory is created!")
    os.system(f'chmod 777 -R {path}')

# Setup the record function

fs = 44100  # Sample rate
# seconds = 3  # Duration of recording
wave_to_send = []

sd.default.samplerate = fs
sd.default.channels = 1

def button_held_handler():
    sd.rec(out=wave_to_send)
    sd.wait()  # Wait until recording is finished

def button_released_handler():
    wavio.write('wave_to_send.wav', wave_to_send, fs, sampwidth=2)  # Save as WAV file
    os.system('aplay ' + path + '/wave_to_send.wav')

# Setup button functions - Pin 27 = Button hold time 10 seconds.

button = Button(27)
button.when_held = button_held_handler
button.when_released = button_released_handler

pause()
