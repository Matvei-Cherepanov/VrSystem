import sqlite3
import os
import sys

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)

from Config import DB_NAME

class Database:
    def __init__(self, db_name=DB_NAME):
        db_full_path = os.path.join(root_path, db_name)
        self.conn = sqlite3.connect(db_full_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            type TEXT NOT NULL,
            service TEXT NOT NULL
        )
        """)
        self.conn.commit()

    def add_booking(self, name, phone, date, time, type, service):
        self.cursor.execute("""
        INSERT INTO bookings (name, phone, date, time, type, service)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (name, phone, date, time, type, service))
        self.conn.commit()

    def get_bookings(self):
        self.cursor.execute("SELECT * FROM bookings")
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()

    def get_all_records(self, limit=None):
        query = '''
        SELECT id,date,time,type as record_type,
               name as client_name,phone as contact
        FROM bookings ORDER BY id DESC
        '''
        if limit:
            query += f" LIMIT {limit}"
        self.cursor.execute(query)
        cols=[d[0] for d in self.cursor.description]
        return [dict(zip(cols,row)) for row in self.cursor.fetchall()]

    def get_record_by_id(self, record_id):
        self.cursor.execute('''
        SELECT id,date,time,type as record_type,
               name as client_name,phone as contact
        FROM bookings WHERE id=?
        ''',(record_id,))
        row=self.cursor.fetchone()
        if not row:
            return None
        cols=[d[0] for d in self.cursor.description]
        return dict(zip(cols,row))

    def update_record(self, record_id, data):
        self.cursor.execute(
            "UPDATE bookings SET name=?, phone=?, date=?, time=?, type=? WHERE id=?",
            (data["client_name"], data["contact"], data["date"], data["time"], data["record_type"], record_id)
        )
        self.conn.commit()

    def delete_record(self, record_id):
        self.cursor.execute("DELETE FROM bookings WHERE id=?", (record_id,))
        self.conn.commit()
