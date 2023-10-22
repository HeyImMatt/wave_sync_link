#!/usr/bin/env python3
from gpiozero import Button
from signal import pause
import sounddevice as sd
import soundfile as sf
import os

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
duration = 5  # Recording duration in seconds

def record_audio(indata, frames, time, status):
    global wave_to_send
    if status:
        print(f"Error in callback: {status}")

    # Convert indata to a copy using memoryview
    indata_copy = memoryview(indata).cast('h')
    wave_to_send = indata_copy.copy()

def play_audio():
    print("Playing sound.")
    os.system('aplay ' + os.path.join(path, 'wave_to_send.wav'))
    print("Playback complete.")

# Setup button functions - Pin 27
button = Button(27)

def button_pressed_handler():
    print("Button held. Recording audio.")
    global wave_to_send
    wave_to_send = None  # Initialize the variable
    stream = sd.RawInputStream(callback=record_audio, channels=1, samplerate=fs)
    stream.start()
    
    # Capture audio while the button is pressed
    while button.is_pressed:
        pass

    stream.stop()
    stream.close()

    if wave_to_send is not None:
        print("Recording stopped. Writing to file.")
        sf.write(os.path.join(path, 'wave_to_send.wav'), wave_to_send, fs)
        print("Writing complete.")
        play_audio()

button.when_pressed = button_pressed_handler

pause()
