import os
import json # Added for handling token.json
import requests
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleAuthRequest # For refreshing token

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive'] # Full Drive access
TOKEN_FILE = 'token.json' # File to store authenticated user's tokens

def get_token():
    """
    Loads Google OAuth2 credentials from token.json.
    Refreshes the access token if it's expired using the refresh token.
    If no valid token exists, it prints an error and exits.
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Check if credentials are valid and if not, try to refresh them
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                # Refresh the token using google.auth's Request object
                creds.refresh(GoogleAuthRequest()) 
            except Exception as e:
                print(f"Error refreshing token: {e}. Token might be revoked or network issue.")
                exit("Authentication token refresh failed. Please generate a new token.json using drive_test.py.")
        else:
            # If no valid creds and no refresh token
            print(f"Error: No valid token found in {TOKEN_FILE}.")
            exit("Authentication token not found or invalid. Please run drive_test.py first to generate token.json.")

        # Save the updated/new credentials
        with open(TOKEN_FILE, 'w') as token_file_obj:
            token_file_obj.write(creds.to_json())

    return creds.token

def find_folder_id_by_name(folder_name):
    """
    Connects to Google Drive API and prints the ID of a specified folder.
    """
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "q": f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
        "fields": "files(id, name)",
        "pageSize": 10
    }
    # Base URL for Google Drive API
    GOOGLE_DRIVE_API = 'https://www.googleapis.com/drive/v3'
    
    response = requests.get(f"{GOOGLE_DRIVE_API}/files", headers=headers, params=params)
    if response.status_code == 200:
        files = response.json().get("files", [])
        if not files:
            print(f"No folder named '{folder_name}' found in your Google Drive.")
        else:
            for f in files:
                print(f"Folder '{f['name']}' ID: {f['id']}")
    else:
        print(f"Error listing folders (HTTP {response.status_code}): {response.text}")

if __name__ == '__main__':
    # Call the function to find IDs for the _requests and _responses folders
    print("Searching for Google Drive folder IDs:")
    find_folder_id_by_name("_requests")
    find_folder_id_by_name("_responses")