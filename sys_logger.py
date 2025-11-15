import psutil
import logging
import os
import time
import atexit
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
import socket
import threading

# Configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']
LOG_FOLDER = 'C://Usage_Logs'
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
UPLOAD_FOLDER_ID = None  # Set this to your Google Drive folder ID

# Create session start timestamp
session_start = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = os.path.join(LOG_FOLDER, f'system_usage_{session_start}.log')

# Set up logging directory
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)

# Set up logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(message)s')

def get_system_usage():
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    return cpu_usage, ram_usage

def log_usage():
    logging.info("Session started")
    while True:
        cpu, ram = get_system_usage()
        logging.info(f"CPU Usage: {cpu}%, RAM Usage: {ram}%")
        time.sleep(60)  # Log every minute

def is_connected():
    try:
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        pass
    return False

def on_exit():
    logging.info("Session ended")

def upload_to_drive():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': os.path.basename(LOG_FILE),
        'parents': [UPLOAD_FOLDER_ID] if UPLOAD_FOLDER_ID else []
    }
    media = MediaFileUpload(LOG_FILE, mimetype='text/plain')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print('File ID: %s' % file.get('id'))

    # Delete the log file locally after successful upload
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

def main():
    atexit.register(on_exit)

    # Start logging thread
    logging_thread = threading.Thread(target=log_usage)
    logging_thread.daemon = True
    logging_thread.start()

    while True:
        if is_connected():
            try:
                upload_to_drive()
                # Log file deleted after upload
            except Exception as e:
                logging.error(f"Upload failed: {e}")
        time.sleep(3600)  # Check for upload every hour

if __name__ == "__main__":
    main()