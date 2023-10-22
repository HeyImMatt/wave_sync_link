#!/usr/bin/env python3
from gpiozero import Button
from signal import pause
import sounddevice as sd
import os
import wave
import array

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

# LOA: Obviously the fuzzed up audio, but also it seems like not holding the
# button down the whole time causes it to crash. Short term may need to add 
# a handler for release so it doesn't crap out.

sd.default.samplerate = fs
sd.default.channels = 1
sd.default.dtype = 'int16'

def write_wav_file(data, sample_rate, filename):
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 16-bit sample width
        wav_file.setframerate(sample_rate)

        # Convert data to a byte array and write to the WAV file
        byte_data = array.array('h', data)  # 'h' represents signed short (16-bit)
        wav_file.writeframes(byte_data.tobytes())

def button_pressed_handler():
    print(f"Recording for {duration} seconds... Release the button to stop recording.")
    wave_to_send = sd.rec(int(duration * fs))
    sd.wait()  # Wait until recording is finished

    print("Recording stopped. Writing to file.")
    write_wav_file(wave_to_send, fs, os.path.join(path, 'wave_to_send.wav'))

    print("Writing complete. Playing sound.")
    os.system('aplay ' + os.path.join(path, 'wave_to_send.wav'))

    print("Playback complete.")

def button_released_handler():
    print("Button Released.")
#     wavio.write(path + '/wave_to_send.wav', wave_to_send, fs, sampwidth=2)  # Save as WAV file
#     os.system('aplay ' + path + '/wave_to_send.wav')
#     print("Playback complete.")

# Setup button functions - Pin 27

button = Button(27)
button.when_pressed = button_pressed_handler
# button.when_held = button_held_handler
button.when_released = button_released_handler

pause()
