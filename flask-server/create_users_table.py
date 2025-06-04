# create_users_table.py
import sqlite3

conn = sqlite3.connect("Smartboard.db")
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
''')

conn.commit()
conn.close()
print("✅ users 테이블 (email 기반) 생성 완료")
