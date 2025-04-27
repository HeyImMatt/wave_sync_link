from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import credentials, storage
from google.cloud import pubsub_v1
import time
import threading

from env_vars import HOME_PATH, FIREBASE_KEY_PATH, STORAGE_BUCKET, PROJECT_NAME, SUBSCRIPTION_NAME, SENDER_NAME, UPLOAD_PATH

if not FIREBASE_KEY_PATH:
    raise Exception("FIREBASE_KEY_PATH environment variable not set.")

credential = credentials.Certificate(f'{HOME_PATH}/{FIREBASE_KEY_PATH}')

app = firebase_admin.initialize_app(credential, options={
    'storageBucket': STORAGE_BUCKET
})

bucket = storage.bucket(name=STORAGE_BUCKET, app=app)

def subscribe_to_topic(wave_received_handler, on_connection_lost=None, on_connection_restored=None):
    subscriber = pubsub_v1.SubscriberClient.from_service_account_file(f'{HOME_PATH}/{FIREBASE_KEY_PATH}')
    subscription_path = subscriber.subscription_path(
        project=PROJECT_NAME, subscription=SUBSCRIPTION_NAME
    )

    def callback(message):
        message.ack()
        attributes = message.attributes
        print(f"Received message: {attributes}")

        blob_path = attributes["objectId"]
        wave_received_blob = bucket.get_blob(blob_path)
        wave_received_handler(wave_received_blob, blob_path)

    def start_streaming():
        print(f"Listening for messages on {subscription_path}...")
        streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
        return streaming_pull_future

    def message_listener():
        failure_count = 0
        backoff = 5  # seconds
        max_backoff = 300  # 5 minutes
        give_up_after = 3600  # 1 hour
        is_connected = True

        while True:
            streaming_pull_future = start_streaming()
            try:
                streaming_pull_future.result()
            except Exception as e:
                #TODO: Doesn't seem to be excepting when the connection is lost
                print(f"Streaming pull future errored: {e}")
                streaming_pull_future.cancel()

                failure_count += 1
                wait_time = min(backoff * (2 ** (failure_count - 1)), max_backoff)
                total_wait = (2 ** failure_count - 1) * backoff
                print(f"Will retry in {wait_time:.1f} seconds (total downtime so far: {total_wait:.1f} seconds)")

                if is_connected and on_connection_lost:
                    on_connection_lost()
                    is_connected = False

                if total_wait > give_up_after:
                    print("Giving up after too many failures.")
                    break

                time.sleep(wait_time)
            else:
                # If result() exits cleanly somehow, reset failure counter
                if not is_connected and on_connection_restored:
                    on_connection_restored()
                    is_connected = True
                failure_count = 0

    listener_thread = threading.Thread(target=message_listener)
    listener_thread.daemon = True
    listener_thread.start()

def upload_wave(wave_to_send_name):
    try:
        bucket.blob(f'from-{SENDER_NAME}/{wave_to_send_name}').upload_from_filename(f'{HOME_PATH}/{UPLOAD_PATH}/{wave_to_send_name}')
        print(f"File {wave_to_send_name} uploaded to /from-{SENDER_NAME}")
    except Exception as e:
        print(f"Error uploading {wave_to_send_name} to /from-{SENDER_NAME}: {e}")
