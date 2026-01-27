import sqlite3
import os

nilsaha_drive_path = '/Users/nilsaha/Library/CloudStorage/GoogleDrive-sahafamily03@gmail.com/My Drive/IMPORTANT DOCUMENTS/3. NILABRO SAHA/'
db_path = os.path.join(nilsaha_drive_path, 'Databases/nilsaha_personal.db')

def get_connection():
    conn = sqlite3.connect(db_path, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()