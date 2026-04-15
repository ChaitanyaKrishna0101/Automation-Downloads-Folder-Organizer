import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.resolve()
DB_PATH = ROOT_DIR / "automation.db"

def log_event(filename, source, destination):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create table with all 4 required columns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            source TEXT,
            destination TEXT,
            timestamp DATETIME
        )
    """)
    cursor.execute("""
        INSERT INTO history (filename, source, destination, timestamp)
        VALUES (?, ?, ?, datetime('now', 'localtime'))
    """, (filename, str(source), str(destination)))
    conn.commit()
    conn.close()