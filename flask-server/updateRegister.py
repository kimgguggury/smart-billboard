import sqlite3

conn = sqlite3.connect("Smartboard.db")
cursor = conn.cursor()

# 테이블 수정 - 이미 있다면 ALTER TABLE로 추가
cursor.execute("ALTER TABLE users ADD COLUMN company TEXT")

conn.commit()
conn.close()
print("✅ users 테이블에 company 컬럼 추가 완료")
