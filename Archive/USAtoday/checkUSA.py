import sqlite3

db_path = r"C:\Users\PC\Desktop\Masterarbeit\Code\USAtoday\articlesUSAToday.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM articles_index")
count = c.fetchone()[0]
print(f"🧮 Anzahl Artikel in 'articles_index': {count}")

c.execute("SELECT * FROM articles_index LIMIT 5")
print("\n📄 Erste 5 Einträge:")
for row in c.fetchall():
    print(row)

conn.close()
