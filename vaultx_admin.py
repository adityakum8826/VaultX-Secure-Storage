import os
import sqlite3
import ctypes
import shutil
import time
from datetime import datetime

# Enable ANSI colors in Windows terminal
os.system('')

DB_PATH = "vaultx_data.db"


class Color:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Color.CYAN + Color.BOLD + "=" * 60)
    print(" 🛡️  VAULTX - ADVANCED ADMIN RECOVERY CONSOLE ")
    print("=" * 60 + Color.RESET)


def system_status():
    print(Color.CYAN + "\n--- [1] System Status & Security Audit ---" + Color.RESET)
    if not os.path.exists(DB_PATH):
        print(Color.RED + "[!] No database found. VaultX is uninitialized." + Color.RESET)
        return

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Check User Config
            cursor.execute("SELECT password_hint, failed_attempts, lockout_until FROM config WHERE id = 1")
            config = cursor.fetchone()

            if not config:
                print(Color.YELLOW + "[!] Database exists, but no user is configured." + Color.RESET)
                return

            hint, attempts, lockout = config
            current_time = time.time()

            print(f"{Color.BOLD}Master Account Status:{Color.RESET}")
            print(f"  • Password Hint   : {hint if hint else 'None Set'}")
            print(f"  • Failed Attempts : {attempts}/5")

            if current_time < lockout:
                remaining = int((lockout - current_time) / 60)
                print(f"  • Lockout Status  : {Color.RED}LOCKED ({remaining} minutes remaining){Color.RESET}")
            else:
                print(f"  • Lockout Status  : {Color.GREEN}ACTIVE{Color.RESET}")

            # Check Vaults
            cursor.execute("SELECT is_locked, total_files FROM vaults")
            vaults = cursor.fetchall()

            total_vaults = len(vaults)
            locked_vaults = sum(1 for v in vaults if v[0] == 1)
            total_files = sum(v[1] for v in vaults)

            print(f"\n{Color.BOLD}Storage Audit:{Color.RESET}")
            print(f"  • Tracked Vaults  : {total_vaults}")
            print(f"  • Locked Vaults   : {Color.YELLOW}{locked_vaults}{Color.RESET}")
            print(f"  • Secured Files   : {total_files:,}")

    except sqlite3.OperationalError:
        print(Color.RED + "[!] Database schema error." + Color.RESET)


def view_database():
    print(Color.CYAN + "\n--- [2] Internal Vault Records ---" + Color.RESET)
    if not os.path.exists(DB_PATH):
        print(Color.RED + "[!] Database not found." + Color.RESET)
        return

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, original_name, path, is_locked, total_files FROM vaults")
            vaults = cursor.fetchall()

            if not vaults:
                print(Color.YELLOW + "No active vaults found." + Color.RESET)
            else:
                print(
                    f"{Color.BOLD}{'ID':<4} | {'Folder Name':<20} | {'Status':<10} | {'Files':<6} | {'Path'}{Color.RESET}")
                print("-" * 80)
                for v in vaults:
                    status = f"{Color.GREEN}LOCKED{Color.RESET}" if v[3] else f"{Color.RED}UNLOCKED{Color.RESET}"
                    print(f"{v[0]:<4} | {v[1][:18]:<20} | {status:<19} | {v[4]:<6} | {v[2]}")
    except sqlite3.OperationalError:
        print(Color.RED + "[!] Database schema error." + Color.RESET)


def view_activity_logs():
    print(Color.CYAN + "\n--- [3] Security Activity Logs ---" + Color.RESET)
    if not os.path.exists(DB_PATH):
        print(Color.RED + "[!] Database not found." + Color.RESET)
        return

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT action, datetime(timestamp, "localtime") FROM activity_log ORDER BY id DESC LIMIT 15')
            logs = cursor.fetchall()

            if not logs:
                print("No activity recorded yet.")
            else:
                print(f"{Color.BOLD}Showing last 15 actions:{Color.RESET}")
                for action, timestamp in logs:
                    # Color code the actions
                    if "Failed" in action:
                        color = Color.RED
                    elif "Locked" in action or "Added" in action:
                        color = Color.YELLOW
                    else:
                        color = Color.GREEN

                    print(f"  [{timestamp}] {color}{action}{Color.RESET}")
    except sqlite3.OperationalError:
        print(Color.YELLOW + "[!] Activity log table not found (You might be on an older version)." + Color.RESET)


def emergency_backup():
    print(Color.CYAN + "\n--- [4] Emergency Database Backup ---" + Color.RESET)
    if not os.path.exists(DB_PATH):
        print(Color.RED + "[!] Database not found to backup." + Color.RESET)
        return

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"vaultx_emergency_backup_{timestamp}.db"
        shutil.copy2(DB_PATH, backup_name)
        print(f"{Color.GREEN}[SUCCESS] Safely backed up database to: {backup_name}{Color.RESET}")
    except Exception as e:
        print(f"{Color.RED}[ERROR] Could not backup: {e}{Color.RESET}")


def unhide_folder():
    print(Color.CYAN + "\n--- [5] Force Unhide Folder ---" + Color.RESET)
    print("Use this if the app crashed and a folder is stuck invisible in Windows.")
    folder = input("Enter the full exact path of the folder: ").strip("'\" ")

    if os.path.exists(folder):
        try:
            # 0x80 is FILE_ATTRIBUTE_NORMAL in Windows API
            ctypes.windll.kernel32.SetFileAttributesW(folder, 0x80)
            print(f"{Color.GREEN}\n[SUCCESS] The folder '{folder}' is now visible in File Explorer.{Color.RESET}")
        except Exception as e:
            print(f"{Color.RED}\n[ERROR] Could not unhide: {e}{Color.RESET}")
    else:
        print(f"{Color.RED}\n[ERROR] System cannot find the path: {folder}{Color.RESET}")


def factory_reset():
    print(Color.RED + Color.BOLD + "\n--- ⚠️ FACTORY RESET VAULTX ⚠️ ---" + Color.RESET)
    print(Color.YELLOW + "WARNING: This deletes the master password and clears all memory.")
    print("WARNING: Any files currently LOCKED will remain PERMANENTLY ENCRYPTED.")
    print("Use this ONLY if you forgot your password and want to start over." + Color.RESET)

    confirm = input("\nType 'YES' (all caps) to confirm: ")

    if confirm == 'YES':
        try:
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
                print(Color.GREEN + "\n[SUCCESS] Database securely deleted." + Color.RESET)
            else:
                print(Color.CYAN + "\n[INFO] No database found to delete." + Color.RESET)
            print(
                Color.GREEN + "[SUCCESS] VaultX is factory reset. Open the main app to create a new vault." + Color.RESET)
        except PermissionError:
            print(Color.RED + "\n[ERROR] Cannot reset. Please close the main VaultX application first." + Color.RESET)
        except Exception as e:
            print(Color.RED + f"\n[ERROR] Could not reset: {e}" + Color.RESET)
    else:
        print(Color.CYAN + "\n[INFO] Factory reset cancelled. Your data is safe." + Color.RESET)


def main():
    while True:
        print_header()
        print("  1. System Status & Security Audit")
        print("  2. View Internal Vault Records")
        print("  3. View Security Activity Logs")
        print("  4. Emergency Database Backup")
        print("  5. Force Unhide Folder (OS-Level)")
        print(Color.RED + "  6. Factory Reset VaultX" + Color.RESET)
        print("  7. Exit\n")

        choice = input("Select an admin action (1-7): ")

        if choice == '1':
            system_status()
        elif choice == '2':
            view_database()
        elif choice == '3':
            view_activity_logs()
        elif choice == '4':
            emergency_backup()
        elif choice == '5':
            unhide_folder()
        elif choice == '6':
            factory_reset()
        elif choice == '7':
            print(Color.CYAN + "Exiting Admin Console..." + Color.RESET)
            break
        else:
            print(Color.RED + "\n[ERROR] Invalid choice." + Color.RESET)

        input(Color.CYAN + "\nPress Enter to return to main menu..." + Color.RESET)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Color.CYAN + "\n\n[INFO] Force quit detected. Exiting Admin Console gracefully..." + Color.RESET)