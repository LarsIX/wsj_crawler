import os
import sys
import time
import sqlite3
import re

# Dynamically add the parent directory to sys.path for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

from web_scrap_WSJ import WSJScraper
from crawl_WSJ_2023 import WebScrap, get_dates  

DB_PATH = r"articleswsj_2023.db"
YEAR_TO_CRAWL = 2023
WAIT_TIME_BETWEEN_REQUESTS = 7
MAX_ARTICLES_PER_DAY = 30
RUN_CRAWL = False
RUN_SCRAPE = True

# Function to retrieve dates from the database that have less than MAX_ARTICLES_PER_DAY articles scraped
def get_open_days(db_name=DB_PATH):
    conn = sqlite3.connect(db_name)
    c = conn.cursor()
    query = """
        SELECT ai.year, ai.month, ai.day,
               COUNT(a.article_id) as article_count
        FROM articles_index ai
        LEFT JOIN article a ON a.index_id = ai.id
            AND a.corpus IS NOT NULL
            AND a.corpus != ''
            AND a.corpus != 'not found'
        GROUP BY ai.year, ai.month, ai.day
        HAVING article_count < ?
        ORDER BY ai.year, ai.month, ai.day
    """
    c.execute(query, (MAX_ARTICLES_PER_DAY,))
    dates = c.fetchall()
    conn.close()
    return [(y, m, d) for (y, m, d, _) in dates]

if __name__ == "__main__":
    print("🚀 WSJ Scraper starting...")

    # Crawl article links if enabled
    if RUN_CRAWL:
        print("🌐 Crawling article links...")
        ws = WebScrap(db_path=DB_PATH)
        dates_to_crawl = get_dates(YEAR_TO_CRAWL)
        for day, month, year in dates_to_crawl:
            print(f"📅 Crawling {int(day)}-{int(month):02d}-{int(year)}")
            ws.get_elements_from_web(year, month, day, WAIT_TIME_BETWEEN_REQUESTS)
            time.sleep(WAIT_TIME_BETWEEN_REQUESTS)
        print("✅ Crawling finished.")

    # Scrape full article content if enabled
    if RUN_SCRAPE:
        print("📰 Starting article scraping...")
        scraper = WSJScraper(DB_PATH)

        while True:
            open_days = get_open_days()

            if not open_days:
                print("✅ Scraping complete.")
                break

            print(f"📂 Using database path: {os.path.abspath(DB_PATH)}")

            for y, m, d in open_days:
                print(f"\n📆 Scraping articles for {int(y)}-{int(m):02d}-{int(d):02d}")
                articles = scraper.get_article_links(limit=MAX_ARTICLES_PER_DAY, year=y, month=m, day=d)
                for article_id, url in articles:
                    scraper.scrape_article(article_id, url)
                time.sleep(20)  # Pause between scraping days to reduce server load

        scraper.close()

    print("🏁 All tasks completed.")
