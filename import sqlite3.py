import sqlite3

conn = sqlite3.connect('articlesWSJ.db')
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()

print("📋 Tabellen in der Datenbank:")
for t in tables:
    print(" -", t[0])

conn.close()
