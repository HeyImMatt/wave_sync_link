#!/usr/bin/env python3
from gpiozero import Button, PWMLED
from signal import pause
import sounddevice as sd
import soundfile as sf
import os
import numpy as np
import time
import subprocess

from cloud_store import upload_wave, subscribe_to_topic
from env_vars import SENDER_NAME, RECEIVING_FROM_NAME

# Make sure the folder structure exists, and if it does not, create it
path = os.path.expanduser('~') + '/waves'
sender_path = path + f'/from-{SENDER_NAME}'
receiver_path = path + f'/from-{RECEIVING_FROM_NAME}'
favorites_path = receiver_path + '/favorites'
archive_path = receiver_path + '/archive'

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

if not os.path.exists(favorites_path):
    os.makedirs(favorites_path)
    print("The new directory is created!")
    os.system(f'chmod 777 -R {favorites_path}')

if not os.path.exists(archive_path):
    os.makedirs(archive_path)
    print("The new directory is created!")
    os.system(f'chmod 777 -R {archive_path}')

# Check if the user has write access to the directory
if not os.access(path, os.W_OK):
    print(f"Error: No write access to the directory '{path}'. Please check permissions.")
    exit()

def play_random_favorite():
    try:
        favorites = [f for f in os.listdir(favorites_path) if os.path.isfile(os.path.join(favorites_path, f))]
        print('Playing a favorite')
        if favorites:
            green_led.off() # remember off is on
            random_favorite = np.random.choice(favorites)
            os.system('aplay ' + os.path.join(favorites_path, random_favorite))
            green_led.value = low_brightness
        else:
            print("No favorites found.")
    except Exception as e:
        print(f"Error playing favorite: {e}")

def is_connected():
    try:
        # Ping Google's public DNS server to check for internet connectivity
        subprocess.check_call(['ping', '-c', '1', '8.8.8.8'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Connected to the internet")
        return True
    except subprocess.CalledProcessError:
        print("Not connected to the internet. Running in offline mode.")
        return False

if not is_connected():
    green_button = Button(pin=5)

    # Setup LEDs
    low_brightness = 0.9
    green_led = PWMLED(pin=13, initial_value=low_brightness)
    green_button.when_pressed = play_random_favorite
else:
    # Setup buttons
    red_button = Button(pin=26, hold_time=2)
    green_button = Button(pin=5, hold_time=2)

    # Setup LEDs
    low_brightness = 0.9
    red_led = PWMLED(pin=12, initial_value=low_brightness) 
    green_led = PWMLED(pin=13, initial_value=low_brightness)

    def pulse_green_led():
        green_led.pulse(fade_in_time=1, fade_out_time=1, n=None, background=True)

    fs = 44100  # Sample rate
    wave_to_send = np.array([], dtype=np.int16)  # Initialize the variable
    recording = False
    stream = None  # Declare stream as a global variable
    wave_to_send_name = None
    currently_playing_wave = None

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

    def get_received_waves():
        return [f for f in os.listdir(os.path.join(receiver_path)) if os.path.isfile(os.path.join(receiver_path, f))]

    def red_button_when_held_handler():
        global sender_path, wave_to_send, wave_to_send_name, recording, stream, currently_playing_wave, green_button_was_held_for_currently_playing_wave

        if len(wave_to_send) > 0:
            os.remove(os.path.join(sender_path, wave_to_send_name))
            wave_to_send_name = None
            wave_to_send = np.array([], dtype=np.int16)
            print("Send cancelled.")
            red_led.value = low_brightness
            green_led.value = low_brightness
            os.system('aplay ' + 'sounds/message-deleted.wav')
            return
        
        if currently_playing_wave:
            os.rename(os.path.join(receiver_path, currently_playing_wave), os.path.join(archive_path, currently_playing_wave))
            currently_playing_wave = None
            green_button_was_held_for_currently_playing_wave = False
            print("Message archived")
            red_led.value = low_brightness

            # Check if there's more waves to play
            waves = get_received_waves()
            if waves:
                pulse_green_led()
            else: 
                green_led.value = low_brightness

            os.system('aplay ' + 'sounds/message-archived.wav')
            return

        print("Button held. Recording audio.")
        wave_to_send = np.array([], dtype=np.int16)  # Reset the variable
        recording = True
        # TODO add some try/catch around the stream start
        stream = sd.InputStream(callback=record_audio, channels=1, samplerate=fs, clip_off=True)
        stream.start()
        print("Start talking.")
        red_led.off() # Remember, off is on

    def red_button_released_handler():
        global recording, stream, wave_to_send, wave_to_send_name

        if recording:
            recording = False
            # TODO Add error handling in case of problems with the stream or record
            stream.stop()
            stream.close()
            red_led.value = low_brightness
            if len(wave_to_send) > 0:
                print("Recording stopped. Writing to file.")
                red_led.pulse(fade_in_time=1, fade_out_time=1, n=None, background=True)
                pulse_green_led()
                wave_to_send_name = f'{int(time.time())}.wav'
                sf.write(os.path.join(sender_path, wave_to_send_name), wave_to_send, fs)
                print("Writing complete.")
                os.system('aplay ' + 'sounds/message-recorded.wav')
                return

        if len(wave_to_send) > 0:
            print("Playing back recorded message.")
            play_audio()
            os.system('aplay ' + 'sounds/message-recorded.wav')
            return

    red_button.when_held = red_button_when_held_handler
    red_button.when_released = red_button_released_handler

    green_button_was_held_for_currently_playing_wave = False

    def green_button_held_handler():
        global currently_playing_wave, green_button_was_held_for_currently_playing_wave, wave_to_send, wave_to_send_name
        
        if len(wave_to_send) > 0:
            os.system('aplay ' + 'sounds/message-sending.wav')
            upload_wave(wave_to_send_name)
            os.system('aplay ' + 'sounds/message-sent.wav')
            red_led.value = low_brightness
            green_led.value = low_brightness
            wave_to_send_name = None
            wave_to_send = np.array([], dtype=np.int16)
            return

        if currently_playing_wave:
            green_button_was_held_for_currently_playing_wave = True
            os.rename(os.path.join(receiver_path, currently_playing_wave), os.path.join(favorites_path, currently_playing_wave))
            print("Message added to favorites")
            os.system('aplay ' + 'sounds/message-added-to-favs.wav')
            currently_playing_wave = None
            red_led.value = low_brightness

            waves = get_received_waves()
            if waves:
                pulse_green_led()
            else: 
                green_led.value = low_brightness

            return

    def green_button_released_handler():
        global currently_playing_wave, green_button_was_held_for_currently_playing_wave

        # Yield to the record flow
        if len(wave_to_send) > 0:
            return

        if currently_playing_wave and not green_button_was_held_for_currently_playing_wave:
            green_led.off() # Remember, off is on
            os.system('aplay ' + os.path.join(path, receiver_path, currently_playing_wave))
            pulse_green_led()
            os.system('aplay ' + 'sounds/message-played.wav')
            return
        
        if green_button_was_held_for_currently_playing_wave:
            green_button_was_held_for_currently_playing_wave = False


    def green_button_pressed_handler():
        global currently_playing_wave
        
        # Yield to the record flow
        if len(wave_to_send) > 0:
            return
        
        # Looks weird but the released handler takes care of playing a message again
        if currently_playing_wave:
            return

        waves = get_received_waves()

        if not waves:
            play_random_favorite()
            return

        # The released handler plays oldest wav and begins decision flow
        currently_playing_wave = min(waves, key=lambda f: os.path.getmtime(os.path.join(receiver_path, f)))
        pulse_green_led()

    green_button.when_pressed = green_button_pressed_handler
    green_button.when_held = green_button_held_handler
    green_button.when_released = green_button_released_handler

    def wave_received_handler(wave_received_blob, blob_path):
        try: 
            wave_received_blob.download_to_filename(f'{path}/{blob_path}')
            pulse_green_led()
        except Exception as e:
            print(f"Error downloading wave: {e}")

    def on_connection_lost():
        print("Connection lost! Disabling red LED.")
        red_led.on()  # LED OFF
        red_led.value = 0  # ensure it's fully off
        red_button.when_held = None
        red_button.when_released = None

    def on_connection_restored():
        print("Connection restored! Re-enabling red LED.")
        red_led.value = low_brightness
        red_button.when_held = red_button_when_held_handler
        red_button.when_released = red_button_released_handler


    subscribe_to_topic(wave_received_handler, on_connection_lost=on_connection_lost, on_connection_restored=on_connection_restored)

    # Check for unplayed waves
    waves = [f for f in os.listdir(os.path.join(receiver_path)) if os.path.isfile(os.path.join(receiver_path, f))]
    if waves:
        pulse_green_led()

print("Wave Sync Link initialized")

pause()
