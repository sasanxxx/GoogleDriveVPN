import requests
import logging

# Configure logging for better output visualization
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SOCKS_PROXY = "socks5h://127.0.0.1:1080" # Address of our SOCKS5 proxy

def get_web_content(url):
    """
    Fetches web content from a given URL through the SOCKS5 proxy.
    Prints the content or an error message.
    """
    logging.info(f"Attempting to fetch content for URL: {url}")
    proxies = {
        'http': SOCKS_PROXY,
        'https': SOCKS_PROXY # Also for HTTPS if the target site is HTTPS
    }

    try:
        # Send a GET request through the SOCKS5 proxy
        # Increase timeout to allow enough time for data exchange via Drive tunnel
        response = requests.get(url, proxies=proxies, timeout=60) # Increased timeout to 60 seconds

        if response.status_code == 200:
            logging.info(f"Successfully retrieved content for {url}. Status Code: {response.status_code}")
            # Print the content of the page
            print("\n" + "="*50)
            print(f"Content for {url}:")
            print("="*50 + "\n")
            print(response.text) # Display the full page content
            print("\n" + "="*50)
            print("End of Content")
            print("="*50 + "\n")
        else:
            logging.error(f"Failed to retrieve {url}. HTTP Status Code: {response.status_code}")
            logging.error(f"Response text (partial): {response.text[:500]}...") # Display a partial error response

    except requests.exceptions.Timeout:
        logging.error(f"Request to {url} timed out after 60 seconds. This tunnel is slow by nature.")
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred during the request to {url}: {e}", exc_info=True)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == '__main__':
    # Ensure client.py (SOCKS5 proxy) is running on your Windows machine before executing this script.
    
    # Start by testing with a non-filtered, simple HTTP site to confirm tunnel functionality.
    get_web_content("http://example.com") 

    # Once confirmed, you can try a filtered site (HTTP or HTTPS):
    # get_web_content("http://bbcpersian.com") 
    # get_web_content("https://some-filtered-site.com")