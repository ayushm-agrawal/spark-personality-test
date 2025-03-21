"""
Firebase Initialization Module

This module initializes the Firebase Admin SDK using a service account key
loaded from the environment variable 'SERVICE_ACCOUNT_KEY'. It sets up and exports
the Firestore client for use in the application.
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve the Firebase service account key from the environment
service_account_key = os.getenv("SERVICE_ACCOUNT_KEY")
if not service_account_key:
    raise ValueError("SERVICE_ACCOUNT_KEY environment variable not set.")

# Parse the service account key JSON string into a dictionary
key_dict = json.loads(service_account_key)

# Initialize Firebase Admin with the provided credentials
cred = credentials.Certificate(key_dict)
firebase_admin.initialize_app(cred)

# Create a Firestore client instance for database operations
db = firestore.client()
