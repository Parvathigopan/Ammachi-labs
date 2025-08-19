# bot/db.py
import sqlite3
import os

DB_PATH = os.path.join(os.getcwd(), "reminders.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT NOT NULL,
            time TEXT NOT NULL,
            text TEXT NOT NULL,
            tz TEXT NOT NULL
        )
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_reminders_chat_id ON reminders(chat_id)")
    conn.commit()
    conn.close()

def add_reminder(chat_id: str, time: str, text: str, tz: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO reminders (chat_id, time, text, tz) VALUES (?, ?, ?, ?)",
        (chat_id, time, text, tz)
    )
    rid = cur.lastrowid
    conn.commit()
    conn.close()
    return rid

def get_reminders(chat_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, time, text FROM reminders WHERE chat_id = ?", (chat_id,))
    rows = cur.fetchall()
    conn.close()
    return [(row["id"], row["time"], row["text"]) for row in rows]

def delete_reminder(rid: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM reminders WHERE id = ?", (rid,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    return deleted > 0

def clear_reminders(chat_id):
    conn = sqlite3.connect("reminders.db")
    cur = conn.cursor()
    
    # Delete reminders for this chat
    cur.execute("DELETE FROM reminders WHERE chat_id=?", (chat_id,))
    
    # Reset the auto-increment counter for the 'reminders' table
    cur.execute("DELETE FROM sqlite_sequence WHERE name='reminders'")
    
    conn.commit()
    conn.close()


def get_timezone(chat_id: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT tz FROM reminders WHERE chat_id = ? LIMIT 1", (chat_id,))
    row = cur.fetchone()
    conn.close()
    return row["tz"] if row else None

def set_timezone(chat_id: str, tz: str):
    """Update all reminders of this chat with new tz (simple design)."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE reminders SET tz = ? WHERE chat_id = ?", (tz, chat_id))
    conn.commit()
    conn.close()

def get_all_reminders():
    """Used at startup to reschedule all reminders."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id,chat_id,time,text,tz FROM reminders")
    rows = cur.fetchall()
    conn.close()
    return [(row["id"], row["chat_id"], row["time"], row["text"], row["tz"]) for row in rows]
