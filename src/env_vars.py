from dotenv import load_dotenv
import os

load_dotenv()

HOME_PATH = os.path.expanduser("~")
UPLOAD_PATH = os.environ.get("UPLOAD_PATH")
FIREBASE_KEY_PATH = os.environ.get("FIREBASE_KEY_PATH")
STORAGE_BUCKET = os.environ.get("STORAGE_BUCKET")
PROJECT_NAME = os.environ.get("PROJECT_NAME")
SUBSCRIPTION_NAME = os.environ.get("SUBSCRIPTION_NAME")
SENDER_NAME = os.environ.get("SENDER_NAME")
RECEIVING_FROM_NAME = os.environ.get("RECEIVING_FROM_NAME")
