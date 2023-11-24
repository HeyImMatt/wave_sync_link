from dotenv import load_dotenv
import os
import firebase_admin
from firebase_admin import credentials, storage
from google.cloud import pubsub_v1
import time

from env_vars import HOME_PATH, FIREBASE_KEY_PATH, STORAGE_BUCKET, PROJECT_NAME, SUBSCRIPTION_NAME, SENDER_NAME, UPLOAD_PATH

if not FIREBASE_KEY_PATH:
    raise Exception("FIREBASE_KEY_PATH environment variable not set.")

credential = credentials.Certificate(f'{HOME_PATH}/{FIREBASE_KEY_PATH}')

app = firebase_admin.initialize_app(credential, options={
    'storageBucket': STORAGE_BUCKET
})

bucket = storage.bucket(name=STORAGE_BUCKET, app=app)

def subscribe_to_topic(wave_received_handler):
    subscriber = pubsub_v1.SubscriberClient.from_service_account_file(f'{HOME_PATH}/{FIREBASE_KEY_PATH}')
    subscription_path = subscriber.subscription_path(
        project = PROJECT_NAME, subscription = SUBSCRIPTION_NAME
    )

    def callback(message):
        message.ack()
        message.data.decode("utf-8")
        attributes = message.attributes
        print(f"Received message: {attributes}")

        blob_path = attributes["objectId"]
        wave_received_blob = bucket.get_blob(f'{blob_path}')
        wave_received_handler(wave_received_blob, blob_path)

    subscriber.subscribe(subscription_path, callback=callback)

    # The subscriber is non-blocking, so we must keep the main thread from
    # exiting to allow it to process messages in the background.
    print(f"Listening for messages on {subscription_path}")
    while True:
        try:
            time.sleep(5)
        except KeyboardInterrupt:
            break

def upload_wave(wave_to_send_name):
    bucket.blob(f'from-{SENDER_NAME}/{wave_to_send_name}').upload_from_filename(f'{HOME_PATH}/{UPLOAD_PATH}/{wave_to_send_name}')
    print(f"File {wave_to_send_name} uploaded to /from-{SENDER_NAME}")
