import requests

# This script is a simple test to verify the SSL/TLS connection from your Python
# environment to Google API servers using the 'requests' library.
# It helps diagnose underlying SSL/TLS configuration issues (e.g., certificate problems).

try:
    # Attempt to make a GET request to a Google API endpoint over HTTPS.
    # A successful response (even a 404/Not Found) indicates a working SSL connection.
    r = requests.get('https://www.googleapis.com')
    print(f"Status Code: {r.status_code}")
    print("SSL connection successful.")
except requests.exceptions.SSLError as e:
    # Catches specific SSL/TLS errors.
    print(f"SSL Error occurred: {e}")
    print("This indicates a problem with the underlying SSL/TLS connection (e.g., certificate verification failure, network interference).")
except Exception as e:
    # Catches any other unexpected errors.
    print(f"An unexpected error occurred: {e}")