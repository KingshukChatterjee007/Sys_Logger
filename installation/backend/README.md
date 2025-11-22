# System Logger

This script logs CPU, RAM, and GPU usage to a local file and optionally uploads the logs to Google Drive.

## Setup Instructions

### Google Drive Upload Setup (Optional)

To enable log uploads to Google Drive:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable the Google Drive API:
   - Navigate to "APIs & Services" > "Library".
   - Search for "Google Drive API" and enable it.
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials".
   - Click "Create Credentials" > "OAuth 2.0 Client IDs".
   - Choose "Desktop application" as the application type.
   - Download the `credentials.json` file and replace the contents of the existing `credentials.json` in the project root directory.
   - Alternatively, copy the "Client ID" and "Client secret" from the Google Cloud Console and replace the placeholders in `credentials.json`:
     - Replace `"your-client-id.apps.googleusercontent.com"` with your actual Client ID.
     - Replace `"your-project-id"` with your project ID.
     - Replace `"your-client-secret"` with your actual Client secret.
5. Optional: Set the `UPLOAD_FOLDER_ID` in `sys_logger.py` to the ID of your desired Google Drive folder.

### Dependencies

Install required packages:
```
pip install psutil gputil pynvml google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

Note: The script supports comprehensive NVIDIA GPU monitoring via pynvml with per-process GPU memory tracking. AMD GPU presence detection is available but detailed monitoring is limited on Windows systems.

### Usage

Run the script:
```
python sys_logger.py
```

The script will start logging usage data. Press Enter to stop logging and attempt upload (if credentials are configured).

Logs are saved locally in `C://Usage_Logs/` with filenames like `system_usage_YYYY-MM-DD_HH-MM-SS.log`.

### Free Alternatives

If you prefer not to use Google Drive:

1. **Local Storage Only**: Comment out the upload functionality in `sys_logger.py` by modifying the `main()` function to skip the upload step.

2. **Dropbox Upload**:
   - Install dropbox-sdk: `pip install dropbox`
   - Get a Dropbox access token from the [Dropbox App Console](https://www.dropbox.com/developers/apps).
   - Modify `upload_to_drive()` to use Dropbox API instead.

3. **OneDrive Upload**:
   - Use Microsoft Graph API.
   - Requires Azure app registration for OAuth.

4. **FTP/SFTP Upload**:
   - For self-hosted storage, modify the upload function to use ftplib or paramiko.

For any alternative, update the `UPLOAD_FOLDER_ID` and `upload_to_drive()` function accordingly.

### Configuration

Edit the following variables in `sys_logger.py`:
- `LOG_FOLDER`: Directory for log files.
- `UPLOAD_FOLDER_ID`: Google Drive folder ID for uploads (leave as None for root).