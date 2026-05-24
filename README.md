
```markdown
# 🛡️ VaultX - Secure Storage

VaultX is a professional, offline folder encryption and security vault for Windows. Built with a Python backend and a modern HTML/CSS/JS "Glassmorphism" frontend via Eel, VaultX provides enterprise-grade data protection without relying on cloud servers or external API keys.

## ✨ Features

* **Military-Grade Encryption:** Utilizes `cryptography` (AES-256 CTR mode) and PBKDF2 key derivation to securely lock and scramble files at the OS level.
* **Modern UI/UX:** A stunning, liquid-3D glassmorphism interface rendered through a lightweight, borderless desktop window.
* **Zero-Knowledge Architecture:** Your master password is never stored. VaultX uses `bcrypt` hashing with unique cryptographic salts stored in a local, self-contained SQLite database.
* **Advanced Security Policies:**
  * **Anti-Brute Force:** Exponential time-lock penalties after 5 failed login attempts (scales up to 2 hours).
  * **Inactivity Auto-Lock:** Automatically locks the session after 5 minutes of idle time.
* **System Activity Log:** An internal ledger tracking successful logins, failed attempts, and vault modifications.
* **Secure Backup:** One-click database exporter to safely back up your cryptographic maps to external or cloud-synced drives.
* **Admin Recovery Console:** A dedicated CLI tool (`vaultx_admin.py`) for OS-level folder unhiding, database audits, and emergency factory resets.

## 🛠️ Tech Stack

* **Backend:** Python 3
* **Frontend:** HTML5, CSS3, Vanilla JavaScript
* **Bridge:** Eel (Python web framework)
* **Database:** SQLite (Local, serverless)
* **Security:** `cryptography`, `bcrypt`, `secrets`

## 🚀 Installation & Setup

To run VaultX from the source code, ensure you have Python 3 installed on your Windows machine.

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/adityakum8826/VaultX-Secure-Storage.git](https://github.com/adityakum8826/VaultX-Secure-Storage.git)
   cd VaultX-Secure-Storage

```

2. **Install the required dependencies:**
```bash
pip install -r requirements.txt

```


3. **Launch the application:**
```bash
python vaultx_web.py

```



## 📦 Compiling to a Standalone Executable (.exe)

You can package VaultX into a single, portable `.exe` file that can run on any Windows computer without requiring Python to be installed.

Run this command in your terminal:

```bash
pyinstaller --noconsole --onefile --name "VaultX_Pro" --add-data "web;web" vaultx_web.py

```

*Your compiled application will be located inside the newly generated `dist/` folder.*

## 📂 Project Structure

```text
VaultX/
 │── core.py             # Backend engine (AES encryption, SQLite management)
 │── vaultx_web.py       # Eel application launcher and JS-to-Python bridge
 │── vaultx_admin.py     # CLI diagnostic and recovery tool
 │── requirements.txt    # Python dependencies
 │
 └── web/                # Frontend UI assets
      │── index.html     
      │── style.css      
      └── main.js        

```

## ⚠️ Security Disclaimer

VaultX is designed to be highly secure. Because it utilizes genuine cryptographic principles, **there is no backdoor**.

* Do not forget your master password.
* Do not delete the `vaultx_data.db` file without making a secure backup first.
* If you lose your password or your database file, any currently locked folders will remain permanently encrypted and mathematically unrecoverable. Use at your own risk.