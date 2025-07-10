import asyncio
import socket
import time
import struct
import logging
import requests # Required for handling HTTP requests

# Import necessary functions from drive_utils_requests module
from drive_utils_requests import encrypt_data, decrypt_data, upload_file, download_file, list_files_in_folder, delete_file, get_token

# --- Server Configuration ---
# IMPORTANT: Replace these IDs with the actual IDs of your Google Drive folders.
# You can find these IDs using the getID.py script.
REQUESTS_FOLDER_ID = '1CtHCatylPW-Llfoj17vNaLETMPlyjfPt' # Folder where client uploads requests
RESPONSES_FOLDER_ID = '1a4E5NitMH5rn0Feu02uZrfa4KvI1vR3O' # Folder where server uploads responses

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def handle_drive_requests():
    """
    Continuously monitors the _requests folder in Google Drive for new requests,
    processes them by connecting to the internet destination, and uploads responses
    to the _responses folder.
    """
    logging.info(f"Server: Listening for requests in '_requests' folder (ID: {REQUESTS_FOLDER_ID})...")

    while True:
        try:
            # List files in the requests folder, running the blocking operation in a separate thread
            files_in_request_folder = await asyncio.to_thread(list_files_in_folder, REQUESTS_FOLDER_ID)
            
            files_to_process = []
            for file_info in files_in_request_folder:
                # Filter for encrypted request files
                if file_info['name'].endswith('.request.enc'):
                    files_to_process.append(file_info)
            
            # Sort files by creation time to process them in order (oldest first)
            files_to_process.sort(key=lambda x: x['createdTime']) 

            for file_info in files_to_process:
                # Extract session_id and packet_id from the file name
                session_id_part = file_info['name'].split('_')[0]
                packet_id_part = file_info['name'].split('_')[1].split('.')[0]

                logging.info(f"Server: Processing request {file_info['name']} (Session: {session_id_part}, Packet: {packet_id_part})")
                
                # Download the request file content
                content_bytes = await asyncio.to_thread(download_file, file_info['id'])
                if content_bytes:
                    decrypted_data = decrypt_data(content_bytes) # Decrypt the content
                    if decrypted_data:
                        try:
                            # --- Internal Tunnel Protocol (as defined in client.py) ---
                            # First 1 byte: length of destination address (N)
                            # Next 2 bytes: destination port (P)
                            # Next N bytes: destination address (e.g., example.com)
                            # Remaining bytes: actual data
                            
                            # Unpack the header to get destination address and port
                            dest_addr_len = struct.unpack('!B', decrypted_data[0:1])[0]
                            dest_port = struct.unpack('!H', decrypted_data[1:3])[0]
                            dest_addr_bytes = decrypted_data[3 : 3 + dest_addr_len]
                            dest_addr = dest_addr_bytes.decode('utf-8')
                            actual_data = decrypted_data[3 + dest_addr_len:] # Extract the actual data payload

                            logging.info(f"Server: Connecting to {dest_addr}:{dest_port}")
                            
                            # Establish a direct TCP connection to the destination
                            reader, writer = await asyncio.open_connection(dest_addr, dest_port)
                            
                            writer.write(actual_data) # Send the data to the destination
                            await writer.drain() # Ensure data is sent

                            # Read the response from the internet destination
                            response_data = await reader.read(4096) # Read up to 4KB of response
                            writer.close() # Close connection to destination
                            await writer.wait_closed() # Wait for connection to close gracefully

                            if response_data:
                                encrypted_response_data = encrypt_data(response_data) # Encrypt the response
                                # File name format: SessionID_PacketID.response.enc
                                response_file_name = f"{session_id_part}_{packet_id_part}.response.enc"
                                logging.info(f"Server: Uploading response for {session_id_part} to '_responses' ({len(response_data)} bytes)")
                                # Upload the encrypted response file to Google Drive
                                await asyncio.to_thread(upload_file, response_file_name, encrypted_response_data, RESPONSES_FOLDER_ID)
                            else:
                                logging.warning(f"Server: No response data received from {dest_addr}:{dest_port}")

                        except Exception as e:
                            logging.error(f"Server: Error in internal tunnel processing for session {session_id_part}: {e}", exc_info=True)
                        finally:
                            # Always delete the request file from Drive after processing (success or failure)
                            await asyncio.to_thread(delete_file, file_info['id'])
                    else:
                        logging.error(f"Server: Failed to decrypt request for {file_info['name']}. Deleting.")
                        await asyncio.to_thread(delete_file, file_info['id']) # Delete corrupted or undecryptable file
                else:
                    logging.error(f"Server: Failed to download request for {file_info['name']}. Deleting.")
                    await asyncio.to_thread(delete_file, file_info['id']) # Delete if download fails

            await asyncio.sleep(1) # Check for new requests every 1 second (polling interval)

        except requests.exceptions.RequestException as error: # Catch errors specific to the 'requests' library
            logging.error(f'Server: An HTTP/Request error occurred while interacting with Google Drive: {error}', exc_info=True)
            await asyncio.sleep(5) # Wait before retrying on network/API errors
        except Exception as e: # Catch any other unexpected errors
            logging.error(f"Server: An unexpected error occurred: {e}", exc_info=True)
            await asyncio.sleep(5) # Wait before retrying on unexpected errors

if __name__ == '__main__':
    # Run the server's main asynchronous function
    asyncio.run(handle_drive_requests())