import sqlite3

conn = sqlite3.connect("reminders.db")
cur = conn.cursor()

for row in cur.execute("SELECT * FROM reminders"):
    print(row)

conn.close()
