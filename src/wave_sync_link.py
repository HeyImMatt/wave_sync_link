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
sd.default.channels = 2
sd.default.device = 'hw:1,0'

def callback(indata, frames, time, status):
    global wave_to_send
    if status:
        print(f"Error in callback: {status}")
    # Append the recorded audio data to the array
    wave_to_send = np.append(wave_to_send, indata)

def button_held_handler():
    global wave_to_send
    # Clear the existing audio data
    wave_to_send = np.array([])

    # Continue recording and appending to the array as long as the button is held
    with sd.InputStream(samplerate=fs, channels=2, dtype='int16', callback=callback):
        print("Recording... Press and hold the button to continue recording.")
        sd.wait()

def button_released_handler():
    print("Recording stopped. Writing to file and playing sound.")
    wavio.write(path + '/wave_to_send.wav', wave_to_send, fs, sampwidth=2)  # Save as WAV file
    os.system('aplay ' + path + '/wave_to_send.wav')
    print("Playback complete.")

# Setup button functions - Pin 27

button = Button(27)
button.when_held = button_held_handler
button.when_released = button_released_handler

pause()
