import os
import sqlite3
import bcrypt
import ctypes
import time
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import secrets


class SecurityManager:
    CHUNK_SIZE = 64 * 1024

    @staticmethod
    def hash_password(password: str) -> bytes:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))

    @staticmethod
    def verify_password(password: str, hashed: bytes) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed)

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=480000)
        return kdf.derive(password.encode('utf-8'))

    @classmethod
    def encrypt_file(cls, file_path: Path, key: bytes, progress_callback=None):
        nonce = secrets.token_bytes(16)
        cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
        encryptor = cipher.encryptor()
        file_size = os.path.getsize(file_path)
        temp_path = file_path.with_suffix(file_path.suffix + '.vx_tmp')

        processed = 0
        with open(file_path, 'rb') as f_in, open(temp_path, 'wb') as f_out:
            f_out.write(nonce)
            while chunk := f_in.read(cls.CHUNK_SIZE):
                f_out.write(encryptor.update(chunk))
                processed += len(chunk)
                if progress_callback: progress_callback(processed, file_size, file_path.name)
            f_out.write(encryptor.finalize())
        os.replace(temp_path, file_path)

    @classmethod
    def decrypt_file(cls, file_path: Path, key: bytes, progress_callback=None):
        file_size = os.path.getsize(file_path)
        if file_size < 16: return
        temp_path = file_path.with_suffix(file_path.suffix + '.vx_tmp')

        with open(file_path, 'rb') as f_in, open(temp_path, 'wb') as f_out:
            nonce = f_in.read(16)
            cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
            decryptor = cipher.decryptor()
            processed = 16
            while chunk := f_in.read(cls.CHUNK_SIZE):
                f_out.write(decryptor.update(chunk))
                processed += len(chunk)
                if progress_callback: progress_callback(processed, file_size, file_path.name)
            f_out.write(decryptor.finalize())
        os.replace(temp_path, file_path)


class WindowsManager:
    FILE_ATTRIBUTE_HIDDEN = 0x02
    FILE_ATTRIBUTE_SYSTEM = 0x04
    FILE_ATTRIBUTE_NORMAL = 0x80

    @classmethod
    def hide_folder(cls, path: str):
        ctypes.windll.kernel32.SetFileAttributesW(str(path), cls.FILE_ATTRIBUTE_HIDDEN | cls.FILE_ATTRIBUTE_SYSTEM)

    @classmethod
    def unhide_folder(cls, path: str):
        ctypes.windll.kernel32.SetFileAttributesW(str(path), cls.FILE_ATTRIBUTE_NORMAL)


class DatabaseManager:
    def __init__(self, db_path="vaultx_data.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, password_hash BLOB NOT NULL, salt BLOB NOT NULL)''')
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS vaults (id INTEGER PRIMARY KEY AUTOINCREMENT, original_name TEXT NOT NULL, path TEXT NOT NULL UNIQUE, is_locked BOOLEAN NOT NULL CHECK (is_locked IN (0, 1)), total_files INTEGER DEFAULT 0)''')

            # New Activity Log Table
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS activity_log (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

            cursor.execute("PRAGMA table_info(vaults)")
            if "total_files" not in [col[1] for col in cursor.fetchall()]:
                cursor.execute("ALTER TABLE vaults ADD COLUMN total_files INTEGER DEFAULT 0")

            cursor.execute("PRAGMA table_info(config)")
            cols = [col[1] for col in cursor.fetchall()]
            if "password_hint" not in cols: cursor.execute(
                "ALTER TABLE config ADD COLUMN password_hint TEXT DEFAULT ''")
            if "failed_attempts" not in cols: cursor.execute(
                "ALTER TABLE config ADD COLUMN failed_attempts INTEGER DEFAULT 0")
            if "lockout_until" not in cols: cursor.execute("ALTER TABLE config ADD COLUMN lockout_until REAL DEFAULT 0")
            conn.commit()

    # --- NEW ACTIVITY LOGGING ---
    def log_activity(self, action: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('INSERT INTO activity_log (action) VALUES (?)', (action,))
            conn.commit()

    def get_logs(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Gets the last 50 actions, converting UTC to Local Time
            cursor.execute(
                'SELECT action, datetime(timestamp, "localtime") FROM activity_log ORDER BY id DESC LIMIT 50')
            return cursor.fetchall()

    def setup_user(self, password: str, hint: str):
        salt = secrets.token_bytes(16)
        password_hash = SecurityManager.hash_password(password)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT INTO config (id, password_hash, salt, password_hint, failed_attempts, lockout_until) VALUES (1, ?, ?, ?, 0, 0)',
                (password_hash, salt, hint))
            conn.commit()
        self.log_activity("VaultX Initialized")

    def get_hint(self) -> str:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password_hint FROM config WHERE id = 1')
            row = cursor.fetchone()
            return row[0] if row else ""

    def factory_reset(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM config')
            conn.execute('DELETE FROM vaults')
            conn.execute('DELETE FROM activity_log')
            conn.commit()

    def is_setup(self) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM config WHERE id = 1')
            return cursor.fetchone() is not None

    def authenticate(self, password: str, is_silent: bool = False) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password_hash, failed_attempts, lockout_until FROM config WHERE id = 1')
            row = cursor.fetchone()
            if not row: return {"success": False, "msg": "App not configured."}

            pwd_hash, attempts, lockout_until = row
            current_time = time.time()

            if current_time < lockout_until:
                return {"success": False, "locked": True, "time_left": int(lockout_until - current_time)}

            if SecurityManager.verify_password(password, pwd_hash):
                conn.execute('UPDATE config SET failed_attempts = 0, lockout_until = 0 WHERE id = 1')
                conn.commit()
                if not is_silent: self.log_activity("Successful Login")
                return {"success": True}

            if is_silent: return {"success": False, "locked": False, "attempts_left": 5 - attempts}

            attempts += 1
            lockout_target, time_left = 0, 0

            if attempts >= 5:
                penalty = min(10 * (2 ** (attempts - 5)), 7200)
                lockout_target = current_time + penalty
                time_left = penalty

            conn.execute('UPDATE config SET failed_attempts = ?, lockout_until = ? WHERE id = 1',
                         (attempts, lockout_target))
            conn.commit()

            self.log_activity(f"Failed Login Attempt ({attempts}/5)")

            if attempts >= 5: return {"success": False, "locked": True, "time_left": int(time_left)}
            return {"success": False, "locked": False, "attempts_left": 5 - attempts}

    def get_salt(self) -> bytes:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT salt FROM config WHERE id = 1')
            return cursor.fetchone()[0]

    def add_vault(self, path: str, name: str, file_count: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'INSERT OR IGNORE INTO vaults (original_name, path, is_locked, total_files) VALUES (?, ?, 1, ?)',
                (name, path, file_count))
            conn.commit()
        self.log_activity(f"Added new vault: {name}")

    def get_vaults(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, original_name, path, is_locked, total_files FROM vaults')
            return cursor.fetchall()

    def update_vault_status(self, vault_id: int, is_locked: bool):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('UPDATE vaults SET is_locked = ? WHERE id = ?', (int(is_locked), vault_id))
            conn.commit()

    def remove_vault(self, vault_id: int):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM vaults WHERE id = ?', (vault_id,))
            conn.commit()
        self.log_activity(f"Removed a vault from tracker")