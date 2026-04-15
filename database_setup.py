import sqlite3

conn = sqlite3.connect("job_tracker.db")
cursor = conn.cursor()

#users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL
)
""")

#applications table
cursor.execute("""
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    company TEXT,
    role TEXT,
    date_applied TEXT,
    interview_date TEXT,
    deadline TEXT,
    status TEXT,

    FOREIGN KEY (user_id) REFERENCES users(id)
)
""")

conn.commit()
conn.close()

print("Applications and users table created successfully.")
