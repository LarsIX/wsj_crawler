import sqlite3
import time
from web_scrap import Search4Articles
import pandas as pd

# Absoluter Pfad zur DB
DB_PATH = r"C:\Users\PC\Desktop\Masterarbeit\Code\articlesWSJ.db"

# Verbindung aufbauen
conn = sqlite3.connect(DB_PATH)

# SQL: Artikel zählen pro Tag (nur mit echtem Inhalt)
query = """
SELECT ai.year, ai.month, ai.day,
    COUNT(DISTINCT a.article_id) as article_count
FROM articles_index ai
LEFT JOIN article a ON a.index_id = ai.id
    AND a.corpus IS NOT NULL AND a.corpus != '' AND a.corpus != 'not found'
GROUP BY ai.year, ai.month, ai.day
HAVING article_count < 30
ORDER BY ai.year, ai.month, ai.day
"""

# Lade Daten in DataFrame
df = pd.read_sql_query(query, conn)
conn.close()

# Datumsspalte erzeugen 
df['month'] = df['month'].astype(str).str.zfill(2)
df['day'] = df['day'].astype(str).str.zfill(2)
df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'] + '-' + df['day'])

# 📦 Erzeuge Liste von (year, month, day)
# Ensure values are int
df[['year', 'month', 'day']] = df[['year', 'month', 'day']].astype(int)
custom_days = list(df[['year', 'month', 'day']].itertuples(index=False, name=None))

# Ausgabe zur Kontrolle
print("📅 Tage mit weniger als 30 Artikeln:")
print(df[['date', 'article_count']])


def has_enough_articles(year, month, day, db_name=DB_PATH, max_articles=30):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(DISTINCT a.article_id)
        FROM articles_index ai
        LEFT JOIN article a ON a.index_id = ai.id
            AND a.corpus IS NOT NULL AND a.corpus != '' AND a.corpus != 'not found'
        WHERE ai.year = ? AND ai.month = ? AND ai.day = ?
    """, (year, month, day))
    count = c.fetchone()[0]
    conn.close()
    return count >= max_articles

if __name__ == "__main__":
    max_articles_per_day = 30

    print("📅 Starte gezieltes Scraping für benutzerdefinierte Tage...")

    sa = Search4Articles(db_name=DB_PATH)

    for (year, month, day) in custom_days:
        print(f"🔍 Überprüfe {year}-{month:02d}-{day:02d}...")

        if has_enough_articles(year, month, day, max_articles=max_articles_per_day):
            print("✅ Genug Artikel vorhanden – überspringe.")
            continue

        print("🚀 Lade fehlende Artikel...")
        sa.navigation(max_per_day=max_articles_per_day, year=year, month=month, day=day)
        print("✅ Fertig mit diesem Tag.\n")
        time.sleep(10)

    sa.driver.quit()
    print("🏁 Alle angegebenen Tage wurden überprüft.")