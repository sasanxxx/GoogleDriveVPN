import asyncio
import socket
import uuid
import time
import struct
import logging

from drive_utils_requests import (
    encrypt_data, decrypt_data,
    upload_file, download_file,
    list_files_in_folder, delete_file,
    get_token # Although not directly used here, it ensures token validity
)

# --- Client Configuration ---
SOCKS_LISTEN_HOST = '127.0.0.1' # Listen on localhost
SOCKS_LISTEN_PORT = 1080      # Standard SOCKS5 port

# IMPORTANT: Replace with your actual Google Drive folder IDs
# These IDs are obtained when you create the _requests and _responses folders.
# Use a script like getID.py to find them.
REQUESTS_FOLDER_ID = '1CtHCatylPW-Llfoj17vNaLETMPlyjfPt' # Folder where client uploads requests
RESPONSES_FOLDER_ID = '1a4E5NitMH5rn0Feu02uZrfa4KvI1vR3O' # Folder where client downloads responses

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Dictionary to keep track of active SOCKS5 sessions
# key: session_id, value: {'writer': asyncio.StreamWriter, 'last_packet_id': int}
active_sessions = {} 

async def handle_socks5_request(reader, writer):
    """
    Handles incoming SOCKS5 proxy requests from the client (e.g., browser).
    Performs SOCKS5 handshake and then starts the data tunneling process.
    """
    peername = writer.get_extra_info('peername')
    logging.info(f"Accepted connection from {peername}")
    session_id = None # Initialize session_id for finally block

    try:
        # SOCKS5 Handshake - Method Negotiation
        # Client sends: VER(1 byte) | NMETHODS(1 byte) | METHODS(NMETHODS bytes)
        client_hello = await reader.readexactly(2)
        ver, nmethods = client_hello
        if ver != 0x05: # SOCKS version 5 expected
            logging.error(f"Unsupported SOCKS version: {ver} from {peername}")
            writer.close()
            return

        methods = await reader.readexactly(nmethods)
        if 0x00 not in methods: # NO AUTHENTICATION REQUIRED method (0x00)
            logging.error(f"No acceptable authentication method from {peername}")
            writer.write(struct.pack('!BB', 0x05, 0xFF)) # SOCKS5, NO ACCEPTABLE METHODS
            await writer.drain()
            writer.close()
            return

        # Server sends: VER(1 byte) | METHOD(1 byte) (0x00 for no auth)
        writer.write(struct.pack('!BB', 0x05, 0x00)) # SOCKS5, NO AUTHENTICATION REQUIRED
        await writer.drain()

        # SOCKS5 Request - Connection Details
        # Client sends: VER(1) | CMD(1) | RSV(1) | ATYP(1) | DST.ADDR | DST.PORT(2)
        request_header = await reader.readexactly(4)
        ver, cmd, rsv, atyp = request_header
        if ver != 0x05: # SOCKS version 5 expected
             logging.error(f"Unsupported SOCKS version in request: {ver} from {peername}")
             writer.close()
             return
        if cmd != 0x01: # Only CONNECT command (0x01) is supported
            logging.error(f"Unsupported SOCKS5 command: {cmd} from {peername}")
            writer.write(struct.pack('!BBBBB', 0x05, 0x07, 0x00, 0x01, 0x00)) # Command not supported
            await writer.drain()
            writer.close()
            return

        # Read Destination Address and Port
        dest_addr = ""
        if atyp == 0x01: # IPv4 Address
            dest_addr = socket.inet_ntoa(await reader.readexactly(4))
        elif atyp == 0x03: # Domain Name
            domain_len = (await reader.readexactly(1))[0]
            dest_addr = (await reader.readexactly(domain_len)).decode('utf-8')
        elif atyp == 0x04: # IPv6 Address
            dest_addr = socket.inet_ntop(socket.AF_INET6, await reader.readexactly(16))
        else:
            logging.error(f"Unsupported address type: {atyp} from {peername}")
            writer.write(struct.pack('!BBBBB', 0x05, 0x08, 0x00, 0x01, 0x00)) # Address type not supported
            await writer.drain()
            writer.close()
            return

        dest_port = struct.unpack('!H', await reader.readexactly(2))[0]
        logging.info(f"SOCKS5: CONNECT {dest_addr}:{dest_port} from {peername}")

        # Send SOCKS5 Response - Connection Granted
        # Server sends: VER(1) | REP(1) | RSV(1) | ATYP(1) | BND.ADDR(var) | BND.PORT(2)
        writer.write(struct.pack('!BBBB', 0x05, 0x00, 0x00, 0x01) + socket.inet_aton('0.0.0.0') + struct.pack('!H', 0))
        await writer.drain()

        # --- Start Data Tunneling via Google Drive ---
        # Generate a unique session ID for this SOCKS5 connection
        session_id = str(uuid.uuid4())
        active_sessions[session_id] = {'writer': writer, 'last_packet_id': 0}
        
        logging.info(f"Tunnel established for {dest_addr}:{dest_port} with session ID {session_id}")
        
        # Run send and receive tasks concurrently
        await asyncio.gather(
            send_data_to_drive(reader, session_id, dest_addr, dest_port),
            receive_data_from_drive(writer, session_id)
        )

    except asyncio.IncompleteReadError as e:
        # This usually means the client disconnected before sending full handshake/request
        logging.warning(f"SOCKS5 Handshake/Request incomplete from {peername}: {e}")
    except ConnectionResetError:
        logging.warning(f"Client {peername} disconnected unexpectedly (ConnectionResetError).")
    except Exception as e:
        logging.error(f"Error handling SOCKS5 connection from {peername}: {e}", exc_info=True)
    finally:
        if session_id and session_id in active_sessions: # Check if session_id was successfully assigned
            del active_sessions[session_id]
        if not writer.is_closing():
            writer.close()
        logging.info(f"Connection from {peername} closed. Session {session_id if session_id else 'N/A'} ended.")

async def send_data_to_drive(reader, session_id, dest_addr, dest_port):
    """
    Reads data from the SOCKS5 client (e.g., browser) and uploads it to Google Drive.
    Each piece of data becomes an encrypted file in the _requests folder.
    """
    packet_id_counter = 0
    while True:
        try:
            # Read data from the SOCKS5 client (e.g., browser)
            data = await reader.read(4096) # Read up to 4KB of data
            if not data:
                # Client closed connection
                logging.info(f"Client {session_id}: No more data from reader, closing send task.")
                break

            packet_id_counter += 1
            dest_addr_bytes = dest_addr.encode('utf-8')

            # Internal Tunnel Protocol:
            # First 1 byte: length of destination address (N)
            # Next 2 bytes: destination port (P)
            # Next N bytes: destination address (e.g., example.com)
            # Remaining bytes: actual data
            header = struct.pack('!BH', len(dest_addr_bytes), dest_port) + dest_addr_bytes
            
            full_packet = header + data # Combine header with actual data

            encrypted_data = encrypt_data(full_packet) # Encrypt the combined packet
            
            # File name format: SessionID_PacketID.request.enc
            file_name = f"{session_id}_{packet_id_counter}.request.enc"
            
            logging.info(f"Client {session_id}: Uploading packet {packet_id_counter} ({len(data)} bytes) for {dest_addr}:{dest_port}")
            # The upload_file is a blocking call, so run it in a separate thread
            await asyncio.to_thread(upload_file, file_name, encrypted_data, REQUESTS_FOLDER_ID)
            # A short sleep can be added here to avoid flooding the Drive API if needed, e.g., await asyncio.sleep(0.1)
        except ConnectionResetError:
            logging.warning(f"Client {session_id}: Connection reset by peer while sending data.")
            break
        except Exception as e:
            logging.error(f"Client {session_id}: Error sending data to drive: {e}", exc_info=True)
            break

async def receive_data_from_drive(writer, session_id):
    """
    Monitors the _responses folder in Google Drive for new response files
    and sends the decrypted data back to the SOCKS5 client (e.g., browser).
    """
    last_processed_packet_id = 0 # To track which packets have already been sent
    while True:
        try:
            # List files in the responses folder
            # The list_files_in_folder is a blocking call, so run it in a separate thread
            files_response_list = await asyncio.to_thread(list_files_in_folder, RESPONSES_FOLDER_ID)
            
            # Filter files belonging to this session and sort by packet ID
            session_files = []
            for file_info in files_response_list:
                if file_info['name'].startswith(f"{session_id}_") and file_info['name'].endswith('.response.enc'):
                    try:
                        # Extract PacketID from file name (e.g., "sessionID_PacketID.response.enc")
                        parts = file_info['name'].split('_')
                        if len(parts) > 1:
                            current_packet_id = int(parts[1].split('.')[0])
                            session_files.append((current_packet_id, file_info))
                    except (ValueError, IndexError):
                        logging.warning(f"Client {session_id}: Malformed response file name: {file_info['name']}. Deleting.")
                        await asyncio.to_thread(delete_file, file_info['id']) # Delete corrupted file
                        continue
            
            # Sort files by their Packet ID to ensure correct order of delivery
            session_files.sort(key=lambda x: x[0]) 

            for current_packet_id, file_info in session_files:
                if current_packet_id > last_processed_packet_id:
                    logging.info(f"Client {session_id}: Found response packet {current_packet_id} ({file_info['name']})")
                    
                    # Download the response file
                    content_bytes = await asyncio.to_thread(download_file, file_info['id'])
                    if content_bytes:
                        decrypted_data = decrypt_data(content_bytes) # Decrypt the data
                        if decrypted_data:
                            writer.write(decrypted_data) # Send to SOCKS5 client
                            await writer.drain() # Ensure data is written
                            await asyncio.to_thread(delete_file, file_info['id']) # Delete file after successful processing
                            last_processed_packet_id = current_packet_id # Update last processed packet ID
                        else:
                            logging.error(f"Client {session_id}: Failed to decrypt response for {file_info['name']}. Deleting.")
                            await asyncio.to_thread(delete_file, file_info['id']) # Delete if decryption fails
                    else:
                        logging.error(f"Client {session_id}: Failed to download response for {file_info['name']}. Deleting.")
                        await asyncio.to_thread(delete_file, file_info['id']) # Delete if download fails
            
            await asyncio.sleep(1) # Check for new files every 1 second
        except ConnectionResetError:
            logging.warning(f"Client {session_id}: Connection reset by peer while receiving.")
            break
        except Exception as e:
            logging.error(f"Client {session_id}: Error receiving data from drive: {e}", exc_info=True)
            break
    if not writer.is_closing():
        writer.close() # Close the writer (connection to the SOCKS5 client) when the loop ends

async def start_client():
    """Starts the SOCKS5 proxy server."""
    logging.info(f"Starting SOCKS5 proxy on {SOCKS_LISTEN_HOST}:{SOCKS_LISTEN_PORT}")
    # Start the asyncio server that handles incoming SOCKS5 connections
    server = await asyncio.start_server(handle_socks5_request, SOCKS_LISTEN_HOST, SOCKS_LISTEN_PORT)
    
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    # Run the client (SOCKS5 proxy)
    asyncio.run(start_client())