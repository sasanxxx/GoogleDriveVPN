import os.path
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If you modified the Scopes in Google Cloud Console, you should update them here as well.
# For full access to Google Drive:
SCOPES = ['https://www.googleapis.com/auth/drive']

def main():
    """
    Authenticates with Google Drive API and lists the first 10 files.
    This script is primarily used to generate/refresh the token.json file.
    """
    creds = None
    # Path to credentials.json file.
    # Ensure credentials.json is in the same directory as this script.
    credentials_file = 'credentials.json'
    # File to store the user's login information (access and refresh tokens).
    token_file = 'token.json' 

    # Check if token.json exists to load previous login credentials.
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    # If login credentials do not exist or are invalid/expired:
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh the token if it's expired and a refresh token is available.
            creds.refresh(Request())
        else:
            # Initiate the authentication flow if no valid credentials exist.
            # This will open a browser window for user authorization.
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the updated/new login credentials for future use.
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    try:
        # Build the Google Drive API service object.
        service = build('drive', 'v3', credentials=creds)

        # Call the Drive API to list the first 10 files.
        results = service.files().list(pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found in your Google Drive.')
            return
        print('Files found in your Google Drive:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))

    except HttpError as error:
        # Handle API errors.
        print(f'An error occurred with Google Drive API: {error}')

if __name__ == '__main__':
    main()