import sqlite3
import time
from web_scrap_WSJ import Search4Articles

# Absoluter Pfad zur DB
DB_PATH = r"C:\Users\PC\Desktop\Masterarbeit\Code\WSJ\articlesWSJ.db"

def get_open_days(db_name=DB_PATH):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    # Diese Abfrage zählt alle Artikel mit echtem Inhalt pro Tag
    query = """
        SELECT 
            ai.year, ai.month, ai.day,
            COUNT(a.article_id) as article_count
        FROM articles_index ai
        LEFT JOIN article a ON a.index_id = ai.id
            AND a.corpus IS NOT NULL 
            AND a.corpus != '' 
            AND a.corpus != 'not found'
        GROUP BY ai.year, ai.month, ai.day
        HAVING article_count < 30
        ORDER BY ai.year, ai.month, ai.day
    """

    c.execute(query)
    dates = c.fetchall()
    conn.close()

    # Gib nur (year, month, day) zurück – ohne count
    return [(y, m, d) for (y, m, d, _) in dates]

if __name__ == "__main__":
    max_articles_per_day = 30  # max of 30 articles per day

    print("🔄 Starte tagesweises Scraping mit Limit 30 Artikel pro Tag...")
    round_count = 0

    while True:
        open_days = get_open_days()

        if not open_days:
            print("✅ Alle Artikel wurden gescraped.")
            break

        sa = Search4Articles(db_name=DB_PATH)
        sa.navigation(max_per_day=max_articles_per_day)
        sa.driver.quit()

        round_count += 1
        print(f"🧾 Runde {round_count} abgeschlossen.")
        print("⏳ Warte 20 Sekunden bis zur nächsten Runde…\n")
        time.sleep(20)
