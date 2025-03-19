import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from dotenv import load_dotenv

load_dotenv()

service_account_key = os.getenv("SERVICE_ACCOUNT_KEY")
if not service_account_key:
    raise ValueError("SERVICE_ACCOUNT_KEY environment variable not set.")

key_dict = json.loads(service_account_key)
cred = credentials.Certificate(key_dict)
firebase_admin.initialize_app(cred)

db = firestore.client()
