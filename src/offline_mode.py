from gpiozero import Button, PWMLED
import os
import numpy as np

def run_in_offline_mode(favorites_path):
    green_button = Button(5)

    # Setup LEDs
    low_brightness = 0.9
    red_led = PWMLED(pin=12, initial_value=1.0) # off 
    green_led = PWMLED(pin=13, initial_value=low_brightness)

    def play_random_favorite():
        try:
            favorites = [f for f in os.listdir(favorites_path) if os.path.isfile(os.path.join(favorites_path, f))]
            if favorites:
                green_led.off() # remember off is on
                random_favorite = np.random.choice(favorites)
                os.system('aplay ' + os.path.join(favorites_path, random_favorite))
                green_led.value = low_brightness
            else:
                print("No favorites found.")
        except Exception as e:
            print(f"Error playing favorite: {e}")

    green_button.when_pressed = play_random_favorite()
