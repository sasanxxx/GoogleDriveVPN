import uuid
import time
import logging

# Import necessary functions from drive_utils_requests
# We are no longer using drive_utils and googleapiclient.discovery.build
from drive_utils_requests import encrypt_data, decrypt_data, upload_file, download_file, list_files_in_folder, delete_file

# --- Test Configuration ---
# IMPORTANT: Replace these IDs with the actual IDs of your Google Drive folders.
# You can find these IDs using the getID.py script.
REQUESTS_FOLDER_ID = '1CtHCatylPW-Llfoj17vNaLETMPlyjfPt' # ID of the _requests folder
RESPONSES_FOLDER_ID = '1a4E5NitMH5rn0Feu02uZrfa4KvI1vR3O' # ID of the _responses folder

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_client_test():
    """
    Simulates the client side: sends a request and waits for a response
    through Google Drive. This is a synchronous test.
    """
    logging.info("--- Running Client Test ---")
    
    # We directly use folder IDs as they are hardcoded in main client/server
    if not REQUESTS_FOLDER_ID or not RESPONSES_FOLDER_ID:
        logging.error("Error: REQUESTS_FOLDER_ID or RESPONSES_FOLDER_ID are not set. Please update them in the script.")
        return

    session_id = str(uuid.uuid4()) # Unique ID for this test session
    test_message = f"Hello from client! Session: {session_id}, Time: {time.time()}"
    encrypted_message = encrypt_data(test_message.encode('utf-8'))
    
    request_file_name = f"{session_id}_request.enc"
    
    logging.info(f"Client: Uploading request '{test_message}' to '_requests' folder (ID: {REQUESTS_FOLDER_ID})...")
    # Upload file (blocking operation)
    file_id = upload_file(request_file_name, encrypted_message, REQUESTS_FOLDER_ID)
    if not file_id:
        logging.error("Client: Failed to upload request file.")
        return

    logging.info(f"Client: Waiting for response in '_responses' folder (ID: {RESPONSES_FOLDER_ID})...")
    response_found = False
    start_time = time.time()
    # Wait for a response for up to 60 seconds
    while time.time() - start_time < 60 and not response_found:
        time.sleep(5) # Check every 5 seconds
        # List files in the response folder (blocking operation)
        files_in_response_folder = list_files_in_folder(RESPONSES_FOLDER_ID)
        for file_info in files_in_response_folder:
            if file_info['name'].startswith(f"{session_id}_response"):
                logging.info(f"Client: Found response file: {file_info['name']}")
                # Download response content (blocking operation)
                response_content = download_file(file_info['id'])
                if response_content:
                    decrypted_response = decrypt_data(response_content).decode('utf-8')
                    logging.info(f"Client: Decrypted response: {decrypted_response}")
                    # Delete files after successful processing (blocking operation)
                    delete_file(file_info['id']) # Delete response file
                    delete_file(file_id) # Delete original request file
                    response_found = True
                    break
        if not response_found:
            logging.info("Client: No response yet, retrying...")
    
    if not response_found:
        logging.warning("Client: Timed out waiting for response.")
        delete_file(file_id) # Delete request file if no response received
            
    logging.info("--- Client Test Finished ---")

def run_server_test():
    """
    Simulates the server side: waits for requests, processes them, and sends responses
    through Google Drive. This is a synchronous test.
    """
    logging.info("--- Running Server Test ---")

    # We directly use folder IDs as they are hardcoded in main client/server
    if not REQUESTS_FOLDER_ID or not RESPONSES_FOLDER_ID:
        logging.error("Error: REQUESTS_FOLDER_ID or RESPONSES_FOLDER_ID are not set. Please update them in the script.")
        return

    logging.info(f"Server: Waiting for requests in '_requests' folder (ID: {REQUESTS_FOLDER_ID}) (will wait for 60 seconds)...")
    request_processed = False
    start_time = time.time()
    # Wait for a request for up to 60 seconds
    while time.time() - start_time < 60 and not request_processed:
        time.sleep(5) # Check every 5 seconds
        # List files in the requests folder (blocking operation)
        files_in_request_folder = list_files_in_folder(REQUESTS_FOLDER_ID)
        for file_info in files_in_request_folder:
            if file_info['name'].endswith('.enc'): # Process any encrypted file
                logging.info(f"Server: Found request file: {file_info['name']}")
                # Download request content (blocking operation)
                request_content = download_file(file_info['id'])
                if request_content:
                    decrypted_request = decrypt_data(request_content).decode('utf-8')
                    logging.info(f"Server: Decrypted request: {decrypted_request}")
                    
                    # Simulate request processing and response generation
                    response_message = f"Response to: '{decrypted_request}'. Processed by server at {time.time()}"
                    encrypted_response = encrypt_data(response_message.encode('utf-8'))
                    
                    # Response file name should include the session_id from the original request
                    session_id = file_info['name'].split('_')[0]
                    response_file_name = f"{session_id}_response.enc"
                    
                    logging.info(f"Server: Uploading response '{response_message}' to '_responses' folder (ID: {RESPONSES_FOLDER_ID})...")
                    # Upload response file (blocking operation)
                    upload_file(response_file_name, encrypted_response, RESPONSES_FOLDER_ID)
                    delete_file(file_info['id']) # Delete request file after processing
                    request_processed = True
                    break
        if not request_processed:
            logging.info("Server: No requests yet, retrying...")

    if not request_processed:
        logging.warning("Server: Timed out waiting for requests.")
            
    logging.info("--- Server Test Finished ---")


if __name__ == '__main__':
    # This script is for testing purposes only.
    # You can activate either run_client_test() or run_server_test() for individual testing,
    # or run both for a full scenario.
    
    # To run a full test scenario:
    # 1. First, run run_server_test() on your server and let it wait for requests.
    # 2. Then, run run_client_test() on your local machine (Windows).
    
    # Activate one of the following lines to run a specific test:
    run_client_test()
    # run_server_test()