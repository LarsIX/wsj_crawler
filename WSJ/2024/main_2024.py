import sqlite3
import time
import os
import sys

# Dynamically add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(parent_dir)

from crawl_WSJ_2024 import WebCrawl, get_dates
from web_scrap_WSJ import WSJScraper

# === CONFIGURATION ===
DB_PATH = r"articlesWSJ_2024.db"
YEAR_TO_CRAWL = 2024
WAIT_TIME_BETWEEN_REQUESTS = 7  # in seconds
MAX_ARTICLES_PER_DAY = 30
RUN_CRAWL = False   # Set to False if links already crawled
RUN_SCRAPE = True  # Set to False if only crawling links
USE_NEW_SCRAPER = True  # Toggle which scraper to use

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
    if RUN_CRAWL:
        print("🌐 Starting CRAWLING for missing article links...")
        wc = WebCrawl()
        dates_to_crawl = get_dates(YEAR_TO_CRAWL)
        for day, month, year in dates_to_crawl:
            print(f"📅 Crawling {day}-{month}-{year}")
            wc.get_elements_from_web(year, month, day, WAIT_TIME_BETWEEN_REQUESTS)
            time.sleep(WAIT_TIME_BETWEEN_REQUESTS)

    if RUN_SCRAPE:
        print("\n📰 Starting SCRAPING for article content...")
        round_count = 0

        if USE_NEW_SCRAPER:
            scraper = WSJScraper(DB_PATH)
            while True:
                open_days = get_open_days()
                if not open_days:
                    print("✅ All articles have been scraped.")
                    break
                for y, m, d in open_days:
                    print(f"\n📆 Scraping content for {int(y)}-{int(m):02d}-{int(d):02d}")
                    articles = scraper.get_article_links(limit=MAX_ARTICLES_PER_DAY, year=int(y), month=int(m), day=int(d))
                for article_id, url in articles:
                    scraper.scrape_article(article_id, url)
                    time.sleep(20)
                round_count += 1
                print(f"🧾 Round {round_count} completed.")
                print("⏳ Waiting 20 seconds before the next round...\n")
                time.sleep(20)
            scraper.close()
        else:
            while True:
                open_days = get_open_days()
                if not open_days:
                    print("✅ All articles have been scraped.")
                    break
                sa = Search4Articles(db_name=DB_PATH)
                for y, m, d in open_days:
                    print(f"\n📆 Scraping content for {y}-{m:02d}-{d:02d}")
                    sa.navigation(max_per_day=MAX_ARTICLES_PER_DAY, year=y, month=m, day=d)
                    time.sleep(20)  # Wait between days
                sa.driver.quit()
                round_count += 1
                print(f"🧾 Round {round_count} completed.")
                print("⏳ Waiting 20 seconds before the next round...\n")
                time.sleep(20)

    print("🏁 All tasks completed.")
