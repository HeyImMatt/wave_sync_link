#!/usr/bin/env python3
from gpiozero import Button
from signal import pause
import sounddevice as sd
import soundfile as sf
import os
import numpy as np
from datetime import datetime, timedelta

# Make sure that the 'waves' folder exists, and if it does not, create it

path = os.path.expanduser('~') + '/waves'

isExist = os.path.exists(path)

if not isExist:
    os.makedirs(path)
    print("The new directory is created!")
    os.system(f'chmod 777 -R {path}')

# Check if the user has write access to the directory
if not os.access(path, os.W_OK):
    print(f"Error: No write access to the directory '{path}'. Please check permissions.")
    exit()

# Setup the record function

fs = 44100  # Sample rate
wave_to_send = np.array([], dtype=np.int16)  # Initialize the variable
recording = False
stream = None  # Declare stream as a global variable

def record_audio(indata, frames, time, status):
    global wave_to_send
    if status:
        print(f"Error in callback: {status}")

    if recording:
        # Append the new data to the array
        wave_to_send = np.append(wave_to_send, indata.copy())

def play_audio():
    print("Playing sound.")
    os.system('aplay ' + os.path.join(path, 'wave_to_send.wav'))
    print("Playback complete.")

# Setup button functions - Pin 27
button = Button(27)

def button_pressed_handler():
    print("Button held. Recording audio.")
    global wave_to_send, recording, stream
    wave_to_send = np.array([], dtype=np.int16)  # Reset the variable
    recording = True
    stream = sd.InputStream(callback=record_audio, channels=1, samplerate=fs)
    stream.start()
    
    # Capture audio while the button is pressed
    # start_time = datetime.now()
    # timeout = timedelta(seconds=10)  # Adjust the timeout as needed

    # while (datetime.now() - start_time) < timeout:
    #     if not button.is_pressed:
    #         break


def button_released_handler():
    global recording, stream
    if recording:
        recording = False
    stream.stop()
    stream.close()

    if len(wave_to_send) > 0:
        print("Recording stopped. Writing to file.")
        sf.write(os.path.join(path, 'wave_to_send.wav'), wave_to_send, fs)
        print("Writing complete.")
        play_audio()

button.when_pressed = button_pressed_handler
button.when_released = button_released_handler

print("Wave Sync Link initialized")

pause()
