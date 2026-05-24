# VaultX 🛡️
A professional, production-grade secure folder locking and encryption system for Windows OS.

## Features
- **AES-256-GCM Encryption:** True military-grade encryption applied to every file.
- **System-Level Hiding:** Integrates with Windows API (`ctypes`) to make folders invisible to regular users.
- **Intruder Capture:** Silently utilizes the webcam to snap a photo if an incorrect password is entered 3 times.
- **Auto-Lock:** Automatically secures the vault after 5 minutes of inactivity.
- **Multithreading:** Fluid CustomTkinter UI that doesn't freeze during heavy encryption workloads.

## Setup Instructions
1. Install Python 3.10 or higher.
2. Clone this repository or download the source files.
3. Install the dependencies: `pip install -r requirements.txt`
4. Run the application: `python VaultX.py`

## Troubleshooting
- **Cannot see files after decryption?** Ensure you hit the "Refresh" button in Windows Explorer. Windows sometimes caches hidden folder states.
- **Forgot Password?** Because VaultX uses actual PBKDF2HMAC key derivation, **there is no backdoor**. If you lose your password, your locked files are permanently encrypted. 

## Future Enhancements (Roadmap)
- **Face Unlock:** Implementation using `dlib` and `face_recognition` libraries (requires Visual Studio C++ Build Tools).
- **Drag-and-Drop Support:** Requires `TkinterDnD2` C-wrappers for seamless OS file dragging.
- **Cloud Backup:** Integration with AWS S3 / Google Drive API to push encrypted vaults to the cloud.