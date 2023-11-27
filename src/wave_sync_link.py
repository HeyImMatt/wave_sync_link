#!/usr/bin/env python3
from gpiozero import Button, PWMLED
from signal import pause
import sounddevice as sd
import soundfile as sf
import os
import numpy as np
import time

from cloud_store import upload_wave, subscribe_to_topic
from env_vars import SENDER_NAME, RECEIVING_FROM_NAME

# Make sure the folder structure exists, and if it does not, create it
path = os.path.expanduser('~') + '/waves'
sender_path = path + f'/from-{SENDER_NAME}'
receiver_path = path + f'/from-{RECEIVING_FROM_NAME}'

isExist = os.path.exists(path)

if not isExist:
    os.makedirs(path)
    print("The new directory is created!")
    os.system(f'chmod 777 -R {path}')

if not os.path.exists(sender_path):
    os.makedirs(sender_path)
    print("The new directory is created!")
    os.system(f'chmod 777 -R {sender_path}')

if not os.path.exists(receiver_path):
    os.makedirs(receiver_path)
    print("The new directory is created!")
    os.system(f'chmod 777 -R {receiver_path}')

# Check if the user has write access to the directory
if not os.access(path, os.W_OK):
    print(f"Error: No write access to the directory '{path}'. Please check permissions.")
    exit()

# Setup the record function

fs = 44100  # Sample rate
wave_to_send = np.array([], dtype=np.int16)  # Initialize the variable
recording = False
stream = None  # Declare stream as a global variable
wave_to_send_name = None

def record_audio(indata, frames, time, status):
    global wave_to_send
    if status:
        print(f"Error in callback: {status}")

    if recording:
        # Append the new data to the array
        wave_to_send = np.append(wave_to_send, indata.copy())

def play_audio():
    print("Playing sound.")
    os.system('aplay ' + os.path.join(sender_path, wave_to_send_name))
    print("Playback complete.")

# Setup button functions - Pin 27
button = Button(27)

green_button = Button(26)
green_led = PWMLED(12, initial_value=0)

def pulse_led(led):
    led.pulse(fade_in_time=1, fade_out_time=1, n=None, background=True)
    time.sleep(2)  # Add a delay between pulses to make it more visible

def button_pressed_handler():
    print("Button held. Recording audio.")
    global wave_to_send, recording, stream
    wave_to_send = np.array([], dtype=np.int16)  # Reset the variable
    recording = True
    stream = sd.InputStream(callback=record_audio, channels=1, samplerate=fs)
    stream.start()

def button_released_handler():
    global recording, stream, wave_to_send_name
    if recording:
        recording = False
    stream.stop()
    stream.close()

    if len(wave_to_send) > 0:
        print("Recording stopped. Writing to file.")
        wave_to_send_name = f'wave-to-send-{int(time.time())}.wav'
        sf.write(os.path.join(sender_path, wave_to_send_name), wave_to_send, fs)
        print("Writing complete.")
        play_audio()
        upload_wave(wave_to_send_name)

button.when_pressed = button_pressed_handler
button.when_released = button_released_handler

def wave_received_handler(wave_received_blob, blob_path):
    wave_received_blob.download_to_filename(f'{path}/{blob_path}')
    pulse_led(green_led)
    # os.system('aplay ' + os.path.join(path, blob_path))

def play_received_waves():
    print('Green button pressed')
    green_led.on()
    # Get a list of all files in the directory
    files = [f for f in os.listdir(os.path.join(path, receiver_path)) if os.path.isfile(os.path.join(path, f))]
        # Find the most recent .wav file
    most_recent_wav = max(files, key=lambda f: os.path.getmtime(os.path.join(path, f)))
    print(most_recent_wav)
    # Play the most recent .wav file
    wav_file_path = os.path.join(path, most_recent_wav)
    os.system('aplay ' + wav_file_path)
    green_led.off()

green_button.when_pressed = play_received_waves

subscribe_to_topic(wave_received_handler)

print("Wave Sync Link initialized")

pause()
