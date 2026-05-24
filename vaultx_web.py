import os
import shutil
import time
import eel
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from core import DatabaseManager, SecurityManager, WindowsManager

db = DatabaseManager()
session_key = None
eel.init('web')


@eel.expose
def is_setup(): return db.is_setup()


@eel.expose
def do_setup(pwd, hint):
    db.setup_user(pwd, hint)
    return True


@eel.expose
def get_hint(): return db.get_hint()


@eel.expose
def factory_reset():
    db.factory_reset()
    return True


@eel.expose
def do_login(pwd):
    global session_key
    # Pass 'is_silent' if the password is empty (boot check) so we don't spam the logs
    is_silent = pwd == ""
    response = db.authenticate(pwd, is_silent)
    if response.get("success"):
        salt = db.get_salt()
        session_key = SecurityManager.derive_key(pwd, salt)
    return response


@eel.expose
def get_vaults(): return db.get_vaults()


@eel.expose
def remove_vault(vault_id): db.remove_vault(vault_id)


@eel.expose
def get_activity_log():
    return db.get_logs()


@eel.expose
def create_backup():
    """Allows user to copy the database to a Cloud Sync folder."""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    dest = filedialog.askdirectory(title="Select Backup Destination (e.g., Google Drive / OneDrive)")
    root.destroy()

    if dest:
        try:
            backup_name = f"VaultX_Backup_{int(time.time())}.db"
            dest_path = os.path.join(dest, backup_name)
            shutil.copy("vaultx_data.db", dest_path)
            db.log_activity(f"Database backed up to {dest_path}")
            return {"success": True, "path": dest_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    return {"success": False, "error": "Cancelled"}


@eel.expose
def browse_folder():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder_path = filedialog.askdirectory()
    root.destroy()
    return folder_path


@eel.expose
def process_vault(vault_id, path, action, is_new):
    folder = Path(path)
    all_files = []
    if folder.exists():
        for root, _, files in os.walk(folder):
            for f in files: all_files.append(Path(root) / f)

    total_files = len(all_files)
    name = os.path.basename(path)

    try:
        if total_files > 0:
            for index, file_path in enumerate(all_files, start=1):
                def progress_cb(current, total, fname):
                    percent = current / total if total > 0 else 1
                    eel.updateProgressUI(percent, f"File {index}/{total_files}: {fname[:35]}...")()

                if action == "lock":
                    SecurityManager.encrypt_file(file_path, session_key, progress_callback=progress_cb)
                else:
                    SecurityManager.decrypt_file(file_path, session_key, progress_callback=progress_cb)
        else:
            eel.updateProgressUI(1.0, "Empty Folder Secured")()
            eel.sleep(0.5)

        if action == "lock":
            WindowsManager.hide_folder(str(folder))
            if is_new:
                db.add_vault(str(folder), name, total_files)
            elif vault_id:
                db.update_vault_status(vault_id, True)
            db.log_activity(f"Locked vault: {name}")
        else:
            WindowsManager.unhide_folder(str(folder))
            db.update_vault_status(vault_id, False)
            db.log_activity(f"Unlocked vault: {name}")

    except Exception as e:
        print(f"Error processing vault: {e}")


if __name__ == '__main__':
    eel.start('index.html', size=(1050, 700), port=0)