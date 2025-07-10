import ssl
import urllib3

# This script tests SSL/TLS connection to Google API, forcing a minimum TLS version.
# This can help diagnose issues related to TLS version mismatches or SSL/TLS interference.

try:
    # Try to use TLSv1_3 if available, otherwise fall back to TLSv1_2.
    # ssl.PROTOCOL_TLS_CLIENT is generally preferred as it handles common client-side SSL behaviors.
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT) # Includes TLSv1_3 and TLSv1_2 on modern Python
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2 # Set minimum acceptable TLS version to 1.2
    except AttributeError:
        # Fallback for older Python versions that do not have TLSVersion or PROTOCOL_TLS_CLIENT
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2) 

    # Create a PoolManager with the specified SSL context.
    http = urllib3.PoolManager(ssl_context=ctx)
    
    # Make a GET request to a Google API endpoint.
    r = http.request('GET', 'https://www.googleapis.com')
    
    print(f"Status: {r.status}")
    print("SSL connection with forced TLS version successful.")
except ssl.SSLError as e:
    # Catches specific SSL/TLS errors.
    print(f"SSL Error occurred with forced TLS: {e}")
    print("This indicates a persistent issue with SSL/TLS context or environmental interference.")
except Exception as e:
    # Catches any other unexpected errors.
    print(f"An unexpected error occurred: {e}")