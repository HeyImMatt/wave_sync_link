#!/usr/bin/env python3
from gpiozero import Button
from signal import pause
import sounddevice as sd
import os
import wavio
import numpy as np

# Make sure that the 'waves' folder exists, and if it does not, create it

path = os.path.expanduser('~') + '/waves'

isExist = os.path.exists(path)

if not isExist:
    os.makedirs(path)
    print("The new directory is created!")
    os.system(f'chmod 777 -R {path}')

# Setup the record function

fs = 44100  # Sample rate
wave_to_send = np.array([])

sd.default.samplerate = fs
sd.default.channels = 1

# Flag to indicate whether recording is in progress
recording = False

def button_held_handler():
    global recording, wave_to_send

    # If recording is not in progress, start recording
    if not recording:
        print("Recording... Press and hold the button to continue recording.")
        recording = True

        # Clear the existing audio data
        wave_to_send = np.array([])

        # Start recording in a loop until the button is released
        while recording:
            indata, overflowed = sd.rec(int(fs), samplerate=fs, channels=1, dtype='int16', blocking=True)
            wave_to_send = np.append(wave_to_send, indata)

        print("Recording stopped.")

def button_released_handler():
    global recording
    recording = False  # Stop recording when the button is released

    print("Saving the recorded audio to a file...")
    wavio.write(path + '/wave_to_send.wav', wave_to_send, fs, sampwidth=2)  # Save as WAV file
    os.system('aplay ' + path + '/wave_to_send.wav')
    print("Played the recorded audio...")

# Setup button functions - Pin 27 = Button hold time 10 seconds.

button = Button(27)
button.when_held = button_held_handler
button.when_released = button_released_handler

pause()
