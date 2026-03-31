import os
import sqlite3

DB_NAME = os.getenv("DB_NAME", "parking.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            vehicle_plate TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create parking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            working_hours TEXT NOT NULL,
            total_slots INTEGER NOT NULL,
            available_slots INTEGER NOT NULL,
            ev_slots_total INTEGER NOT NULL DEFAULT 0,
            ev_slots_available INTEGER NOT NULL DEFAULT 0,
            accessible_slots_total INTEGER NOT NULL DEFAULT 0,
            accessible_slots_available INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create reservations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            parking_id INTEGER NOT NULL,
            reservation_start DATETIME NOT NULL,
            reservation_end DATETIME NOT NULL,
            status TEXT NOT NULL,
            reservation_code TEXT UNIQUE,
            requires_human_validation BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (parking_id) REFERENCES parking (id)
        )
    ''')

    # Insert default parking record if empty
    cursor.execute("SELECT COUNT(*) FROM parking")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO parking (name, address, working_hours, total_slots, available_slots, ev_slots_total, ev_slots_available, accessible_slots_total, accessible_slots_available)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ("Central Plaza Parking", "15 Liberty Square, Tbilisi, Georgia", "07:00 - 23:00", 120, 120, 10, 10, 5, 5))
        print("Inserted default parking location.")

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()
