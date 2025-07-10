from cryptography.fernet import Fernet

# This script generates a new Fernet encryption key.
# This key is crucial for securing data transmitted between the client and server.
# It must be identical on both client.py and server.py.
key = Fernet.generate_key()
print(key.decode())