# This script checks for days in 2024 with fewer than 30 WSJ-articles in the database  and scrapes additional articles for those days.

import sqlite3
import pandas as pd
from scraper_module import WebScrap 

# DB path
DB_PATH = r"C:\Users\PC\Desktop\Masterarbeit\Code\articlesWSJ.db"

# ind days in 2024 with fewer than 30 articles 
def get_days_with_incomplete_articles_2024(db_path, min_articles=30):
    conn = sqlite3.connect(db_path)
    query = """
    SELECT ai.year, ai.month, ai.day,
           COUNT(DISTINCT a.article_id) as article_count
    FROM articles_index ai
    LEFT JOIN article a ON ai.id = a.index_id
        AND a.corpus IS NOT NULL AND a.corpus != '' AND a.corpus != 'not found'
    WHERE ai.year = 2024
    GROUP BY ai.year, ai.month, ai.day
    HAVING article_count < ?
    ORDER BY ai.year, ai.month, ai.day
    """
    df = pd.read_sql_query(query, conn, params=(min_articles,))
    conn.close()
    return df

# Scrape new links for the missing days
def scrape_missing_links_2024(df_days, db_path, wait_time=5):
    scraper = WebScrap(db_name=db_path)  

    for _, row in df_days.iterrows():
        year = int(row["year"])
        month = int(row["month"])
        day = int(row["day"])

        print(f"🔗 Scanning for additional links: {day:02d}.{month:02d}.{year}")
        scraper.get_elements_from_web(year, month, day, waiting_time=wait_time)

    print("✅ Done adding links.")

#  RUN
if __name__ == "__main__":
    df_missing_days = get_days_with_incomplete_articles_2024(DB_PATH, min_articles=30)

    if df_missing_days.empty:
        print("✅ All days in 2024 have 30 or more articles.")
    else:
        print(f"📅 {len(df_missing_days)} days in 2024 need more links/articles.")
        scrape_missing_links_2024(df_missing_days, db_path=DB_PATH, wait_time=5)
