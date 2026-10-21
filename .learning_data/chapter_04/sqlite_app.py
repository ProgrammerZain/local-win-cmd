import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent / "app.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 1. Create Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user'
    );
    """)

    # 2. Create Documents Table with Foreign Key
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """)

    # 3. Seed Users if table is empty
    cursor.execute("SELECT COUNT(*) FROM users;")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO users (username, full_name, role) VALUES (?, ?, ?);
        """, [
            ("alice", "Alice Wonderland", "engineer"),
            ("bob", "Bob Builder", "admin")
        ])
        print("[INFO] Seeded users table (Alice, Bob).")

    conn.commit()
    conn.close()

def list_users():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, role FROM users;")
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    users = list_users()
    print("\nRegistered Users in SQLite:")
    print("-" * 40)
    for u in users:
        print(f"ID: {u[0]} | Username: {u[1]:<10} | Name: {u[2]:<18} | Role: {u[3]}")
