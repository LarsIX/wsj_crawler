"""
WSJ Missing Data Recovery Script  
---------------------------------
- Identifies dates with incomplete article coverage based on a CSV of missing days.  
- Step 1 (Optional): Scrapes missing article links using WebScrap.  
- Step 2: Downloads full article content using Search4Articles (headless browser).  
- Ensures database completeness by targeting days with fewer than `MAX_ARTICLES_PER_DAY` valid articles.  
- Requires: 
    - missing_dates.csv (list of dates to check)
    - articlesWSJ_final_clean_2024.db (final database)  
"""

import time
import pandas as pd
import sqlite3
from scrape_missing_days_WSJ_2024 import WebScrap

# Dynamically add the parent directory to sys.path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from web_scrap_WSJ import Search4Articles

# === Paths ===
DB_PATH = r"articlesWSJ_final_clean_2024.db"
CSV_PATH = r"missing_dates.csv"

# === Config switches ===
RUN_SCRAPE_LINKS = False
RUN_SCRAPE_ARTICLES = True
MAX_ARTICLES_PER_DAY = 30


def load_missing_dates_from_csv(csv_path):
    df = pd.read_csv(csv_path)
    dates = df['date'].dropna().unique()
    return [tuple(map(int, d.split('-'))) for d in dates]


def filter_dates_with_missing_articles(all_dates, final_clean_db, threshold=30):
    """Return only dates with fewer than `threshold` valid articles in the final DB."""
    conn = sqlite3.connect(final_clean_db)
    query = """
        SELECT ai.year, ai.month, ai.day, COUNT(*) as count
        FROM articles_index ai
        JOIN article a ON ai.id = a.index_id
        WHERE a.corpus IS NOT NULL AND a.corpus != '' AND a.corpus != 'not found'
        GROUP BY ai.year, ai.month, ai.day
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    counts = {(int(r['year']), int(r['month']), int(r['day'])): int(r['count']) for _, r in df.iterrows()}
    return [d for d in all_dates if counts.get(d, 0) < threshold]


def scrape_links(missing_dates, max_articles=30, wait_time=7):
    print("\n🔗 STEP 1: Sammle Artikel-Links...")
    ws = WebScrap(db_path=DB_PATH)

    for y, m, d in missing_dates:
        print(f"📆 {y}-{m:02d}-{d:02d}: Sammle max {max_articles} Links")
        ws.get_elements_for_day_filtered(year=y, month=m, day=d, max_articles=max_articles, waiting_time=wait_time)
        print("⏳ Warte 10 Sekunden...\n")
        time.sleep(10)


def scrape_articles(missing_dates, max_articles=30):
    print("\n📰 STEP 2: Lade Inhalte zu Artikeln...")
    for y, m, d in missing_dates:
        print(f"\n📆 {y}-{m:02d}-{d:02d}: Artikelinhalt herunterladen...")
        sa = Search4Articles(db_name=DB_PATH)
        sa.navigation(max_per_day=max_articles, year=y, month=m, day=d)
        sa.driver.quit()
        print("⏳ Warte 20 Sekunden...\n")
        time.sleep(20)


if __name__ == "__main__":
    all_dates = load_missing_dates_from_csv(CSV_PATH)
    filtered_dates = filter_dates_with_missing_articles(all_dates, DB_PATH, threshold=MAX_ARTICLES_PER_DAY)

    if RUN_SCRAPE_LINKS:
        scrape_links(filtered_dates, max_articles=MAX_ARTICLES_PER_DAY)

    if RUN_SCRAPE_ARTICLES:
        scrape_articles(filtered_dates, max_articles=MAX_ARTICLES_PER_DAY)
