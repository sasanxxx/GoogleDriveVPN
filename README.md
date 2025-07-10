# Google Drive SOCKS5 Proxy: A Censorship Circumvention Tool

![Python](https://img.shields.io/badge/Python-3.x-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

## Introduction

This project implements a **SOCKS5 proxy** that tunnels internet traffic through the **Google Drive API**. It offers a novel and highly censorship-resistant way to access the internet, as its traffic appears as regular Google Drive activity, making it difficult for censorship systems to detect and block.

This tool is designed as a **Proof of Concept (PoC)** demonstrating the feasibility of using cloud storage APIs for secure, obfuscated tunneling.

## Features

* **Censorship-Resistant:** Traffic is disguised as legitimate Google Drive API requests (upload/download of small encrypted files).
* **Encrypted Communication:** All data transferred through the tunnel is encrypted using Fernet symmetric encryption (`cryptography` library).
* **SOCKS5 Proxy Support:** Compatible with applications and browsers that support SOCKS5 proxy configuration.
* **Cross-Platform (Python-based):** Client runs on Windows, server runs on Linux (e.g., Ubuntu VPS).
* **Self-Hosted:** You control your own proxy server without relying on third-party VPN providers.

## Limitations

Due to the inherent nature of file-based data transfer via a cloud storage API, this proxy has significant limitations in terms of speed and latency:

* **Low Speed:** It is **inherently slow** compared to traditional VPNs (WireGuard, OpenVPN, etc.). Each data packet requires file upload/download operations on Google Drive, introducing considerable latency.
* **Not for General Browse/Streaming:** It is **not suitable for general web Browse, video streaming, large file downloads, or online gaming.** Modern browsers and applications often time out due to the high latency.
* **Best for Emergency Access:** This tool is best used for **emergency access to critical filtered websites (e.g., text-heavy news sites) or for low-bandwidth communication like text-based messaging applications** where speed is not the primary concern.

## How It Works (Conceptual Overview)

1.  **SOCKS5 Client (Your Machine):** Your browser or application sends traffic to the local SOCKS5 proxy (`127.0.0.1:1080`).
2.  **Data Tunneling via Google Drive:**
    * The client splits the traffic into small chunks, encrypts them, and uploads them as files to a designated `_requests` folder in your Google Drive.
    * The server continuously monitors this folder, downloads the request files, decrypts them, and sends the actual internet traffic to the destination (e.g., `google.com`).
    * The server receives the response from the internet, encrypts it, and uploads it as files to a `_responses` folder in your Google Drive.
    * The client continuously monitors the `_responses` folder, downloads the response files, decrypts them, and sends the data back to your browser/application.
3.  **Real Internet Access (Your Server):** The Ubuntu VPS acts as the gateway to the internet, processing requests and forwarding responses.

## Prerequisites

Before you begin, ensure you have the following:

* **Python 3.x** installed on both your local machine (Windows) and your remote server (Ubuntu VPS).
* **`pip`** (Python package installer) installed with Python.
* A **Google Account** (to use Google Drive API).
* A **remote Linux server** (e.g., Ubuntu VPS in a non-filtered location like Hong Kong) to act as your proxy server.
* Basic familiarity with Command Prompt/PowerShell (Windows) and SSH (Linux).

## Setup Guide (Step-by-Step)

Follow these steps carefully to set up your Google Drive SOCKS5 Proxy.

### **Step 1: Enable Google Drive API & Get Credentials**

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/). Log in with your Google Account.
2.  Create a new project (e.g., `MyDriveVPN`) from the project dropdown at the top.
3.  In the search bar, type "Google Drive API" and select it. Click "Enable".
4.  Navigate to **APIs & Services > Credentials**.
5.  Click **"+ CREATE CREDENTIALS"** and choose **"OAuth client ID"**.
6.  If prompted, configure the **OAuth Consent Screen**:
    * Select "External" User Type.
    * Provide an "App name" (e.g., `DriveVPN Client`) and your "User support email".
    * In the "Scopes" section, click "ADD OR REMOVE SCOPES", search for `drive`, and select the `.../auth/drive` scope (full Drive access). Click "UPDATE".
    * In the "Test users" section, click "ADD USERS" and add **your own Google account email**. This is crucial for testing the unverified app.
    * Save and go back to the dashboard.
7.  Return to **APIs & Services > Credentials**. Click **"+ CREATE CREDENTIALS"** again and choose **"OAuth client ID"**.
8.  Select **"Desktop app"** as the Application type. Give it a name (e.g., `DriveVPN Desktop Client`). Click "CREATE".
9.  A small window will pop up showing your Client ID and Client Secret. Click **"DOWNLOAD JSON"** and save the file as `credentials.json` in your project folder (`MyDriveVPN_Project`). **Keep this file secure and NEVER share it publicly.**

### **Step 2: Install Python Dependencies**

Install required Python libraries on **both your Windows machine (client)** and your **Ubuntu VPS (server)**.

* **On your Windows machine (in Command Prompt/PowerShell in your project folder):**
    ```bash
    pip install requests cryptography google-auth-oauthlib
    pip install requests[socks] # Essential for SOCKS5 proxy support
    ```
* **On your Ubuntu VPS (via SSH):**
    ```bash
    sudo apt update
    sudo apt install python3-pip # Ensure pip is installed for python3
    pip3 install requests cryptography google-auth-oauthlib
    ```

### **Step 3: Generate & Transfer Authentication Token (`token.json`)**

This script authenticates your application and generates `token.json`, which stores your access and refresh tokens.

1.  **Place `credentials.json`:** Ensure the `credentials.json` file you downloaded in Step 1 is in your `MyDriveVPN_Project` folder on your **Windows machine**.
2.  **Generate `token.json`:**
    * Open Command Prompt/PowerShell in your `MyDriveVPN_Project` folder (Windows).
    * Run the `drive_test.py` script:
        ```bash
        python drive_test.py
        ```
    * This will open a browser tab asking you to authorize your `DriveVPN Client` app. **Authorize the access.**
    * After successful authorization, the browser tab will confirm, and `drive_test.py` will list some of your Drive files in the console. A `token.json` file will be created in your project folder.
3.  **Transfer `token.json` to your Ubuntu VPS:**
    * Open a **new** Command Prompt/PowerShell window (Windows).
    * Use `scp` to securely copy `token.json` to your VPS:
        ```bash
        scp "C:\Users\YourUsername\YourProjectPath\token.json" username@your_server_ip:~/MyDriveVPN_Project/token.json
        ```
        * Replace `YourUsername`, `YourProjectPath`, `username`, and `your_server_ip` with your actual details.

### **Step 4: Create Google Drive Folders**

You need two specific folders in your Google Drive for the proxy to function.

1.  Go to your [Google Drive](https://drive.google.com/) in your web browser.
2.  Create two new folders directly in your Drive's root:
    * `_requests`
    * `_responses`

### **Step 5: Find Google Drive Folder IDs & Update Scripts**

The client and server scripts use the unique IDs of these folders, not their names.

1.  **Find Folder IDs:**
    * Open Command Prompt/PowerShell in your `MyDriveVPN_Project` folder (Windows).
    * Run the `getID.py` script:
        ```bash
        python getID.py
        ```
    * This will print the IDs for your `_requests` and `_responses` folders (e.g., `Folder '_requests' ID: 1CtHCatylPW-Llfoj17vNaLETMPlyjfPt`). Copy these IDs.
2.  **Update `client.py`:**
    * Open `client.py` in a text editor.
    * Replace `REQUESTS_FOLDER_ID` and `RESPONSES_FOLDER_ID` with the actual IDs you copied:
        ```python
        REQUESTS_FOLDER_ID = 'YOUR_ACTUAL_REQUESTS_FOLDER_ID_HERE'
        RESPONSES_FOLDER_ID = 'YOUR_ACTUAL_RESPONSES_FOLDER_ID_HERE'
        ```
3.  **Update `server.py` (on Ubuntu VPS):**
    * Connect to your Ubuntu VPS via SSH.
    * Navigate to your project folder: `cd MyDriveVPN_Project`.
    * Open `server.py` with `nano`: `nano server.py`.
    * Replace `REQUESTS_FOLDER_ID` and `RESPONSES_FOLDER_ID` with the actual IDs you copied.
    * Save and exit `nano` (Ctrl+X, Y, Enter).

### **Step 6: Generate & Set Encryption Key**

This encryption key secures all data passing through your tunnel. It **must be identical** on both the client and server.

1.  **Generate Key:**
    * Open Command Prompt/PowerShell in your `MyDriveVPN_Project` folder (Windows).
    * Run the `generate_key.py` script:
        ```bash
        python generate_key.py
        ```
    * Copy the output (a long string starting with `b'...'`).
2.  **Update `drive_utils_requests.py` (on Windows):**
    * Open `drive_utils_requests.py` in a text editor.
    * Find the `ENCRYPTION_KEY` line and replace `'YOUR_ACTUAL_ENCRYPTION_KEY_HERE...'` with the key you generated. Ensure it remains a byte string (starts with `b'` and is enclosed in single quotes).
        ```python
        ENCRYPTION_KEY = b'YOUR_COPIED_ENCRYPTION_KEY_HERE'
        ```
3.  **Update `drive_utils_requests.py` (on Ubuntu VPS):**
    * Connect to your Ubuntu VPS via SSH and go to your project folder.
    * Open `drive_utils_requests.py` with `nano`: `nano drive_utils_requests.py`.
    * Replace the `ENCRYPTION_KEY` with the exact same key you used on Windows.
    * Save and exit `nano`.

## Usage Guide

Once setup is complete, you can start using your Google Drive SOCKS5 Proxy.

### **1. Run the Server (on your Ubuntu VPS)**

* Connect to your Ubuntu VPS via SSH.
* Navigate to your project folder: `cd MyDriveVPN_Project`.
* Run the server script:
    ```bash
    python3 server.py
    ```
    Leave this terminal open and running. It will start listening for requests from Google Drive.

### **2. Run the Client (on your Windows Machine)**

* Open Command Prompt/PowerShell in your `MyDriveVPN_Project` folder (Windows).
* Run the client script:
    ```bash
    python client.py
    ```
    Leave this terminal open and running. It will start the local SOCKS5 proxy on `127.0.0.1:1080`.

### **3. Configure Your Application (Browser/Command Line Tool)**

Now you can configure your applications to use your local SOCKS5 proxy.

* **For Browsers (Recommended: Firefox or Chrome with Proxy Extensions):**
    * **Firefox:**
        1.  Go to `Settings` > `General` > `Network Settings` > `Settings...`.
        2.  Select `Manual proxy configuration`.
        3.  In the `SOCKS Host` field, enter `127.0.0.1`. In the `Port` field, enter `1080`.
        4.  Select `SOCKS v5`.
        5.  Click `OK`.
    * **Chrome (with extensions like Proxy SwitchyOmega):**
        1.  Install a proxy management extension (e.g., Proxy SwitchyOmega).
        2.  Create a new proxy profile.
        3.  Set the Protocol to `SOCKS5`.
        4.  Set the Server to `127.0.0.1` and Port to `1080`.
        5.  Apply changes and select this proxy profile.
    * **Important:** Disable any system-wide proxy settings in Windows (`Settings > Network & internet > Proxy`) when using browser-specific proxy settings.

* **For Command Line Tools (e.g., `curl`):**
    This is the best way to quickly test and confirm data transfer due to its simplicity.
    * Open a **new** Command Prompt (CMD) window (Windows).
    * Run `curl` using your SOCKS5 proxy:
        ```bash
        curl -x socks5h://127.0.0.1:1080 [http://example.com](http://example.com)
        ```
        (Replace `http://example.com` with a filtered HTTP/HTTPS website to test circumvention.)
    * If successful, you will see the HTML content of the website printed in your terminal.

## Utility Scripts

The project includes several utility scripts to help with setup and testing:

* `drive_test.py`: Verifies Google Drive API connection and generates/refreshes `token.json`.
* `generate_key.py`: Generates a new Fernet encryption key.
* `getID.py`: Finds the Google Drive IDs for your `_requests` and `_responses` folders.
* `refresh.py`: Manually refreshes your Google Drive access token (useful for debugging, automatic refresh is built-in).
* `simple_web_client.py`: A basic command-line web client to test Browse via the SOCKS5 proxy.
* `test_communication.py`: Tests the end-to-end data transfer (upload/download/encrypt/decrypt) between client and server via Google Drive.
* `test_ssl_simple.py`: Checks basic SSL/TLS connection to Google APIs.
* `test_ssl_tls_force.py`: Checks SSL/TLS connection forcing specific TLS versions.

## Security Considerations

* **`credentials.json` and `token.json`:** These files contain sensitive authentication information for your Google Account. **NEVER share them, commit them to Git, or expose them publicly.** Your `.gitignore` file is configured to exclude them.
* **Encryption Key:** The `ENCRYPTION_KEY` (in `drive_utils_requests.py`) is crucial for securing your data. **Generate your own unique key and do not use the default one for real traffic.** Keep it confidential.
* **VPS Security:** Ensure your Ubuntu VPS is secure (e.g., strong SSH passwords/keys, firewall rules, regular updates).

## Contributing

Contributions are welcome! If you find bugs, have suggestions for improvements (especially regarding speed optimization or new features like Push Notifications), or want to add to the documentation, feel free to:

1.  Open an [Issue](https://github.com/sasanxxx/GoogleDriveVPN/issues) to report bugs or suggest ideas.
2.  Fork the repository and submit a [Pull Request](https://github.com/sasanxxx/GoogleDriveVPN/pulls) with your changes.

---

**[MIT License](LICENSE)**
