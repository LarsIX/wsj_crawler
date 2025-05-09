import os
import time
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

DB_PATH = r"C:\Users\PC\Desktop\Masterarbeit\Code\LATimes\articlesLAT.db"

ALLOWED_SECTIONS = [
    "/world-nation/",
    "/business/",
    "/opinion/",
    "/california/",
    "/politics/"
]
EXCLUDED_SECTIONS = [
    "/homeless-housing/",
    "/science/medicine/"
]

class LATimesDB:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()

    def insert(self, entry):
        self.c.execute("SELECT 1 FROM articles_index WHERE link = ?", (entry["link"],))
        if self.c.fetchone():
            print(f"⚠️ Already exists: {entry['link']}")
            return False

        self.c.execute("""
            INSERT INTO articles_index 
            (headline, article_time, year, month, day, keyword, link, scraped_at, scanned_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry["headline"], entry["article_time"], entry["year"], entry["month"],
            entry["day"], entry["keyword"], entry["link"], entry["scraped_at"], entry["scanned_status"]
        ))
        self.conn.commit()
        return True

    def close(self):
        self.conn.close()

def is_allowed_section(href):
    return any(section in href for section in ALLOWED_SECTIONS) and not any(excl in href for excl in EXCLUDED_SECTIONS)

def fetch_page_source_with_browser(url):
    options = Options()
    options.add_argument("user-data-dir=C:/Users/PC/AppData/Local/Google/Chrome/User Data")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        time.sleep(3)
        return driver.page_source
    finally:
        driver.quit()

def fetch_article_date(url):
    try:
        html = fetch_page_source_with_browser(url)
        soup = BeautifulSoup(html, "html.parser")
        date_tag = soup.find("span", class_="published-date-day")
        if date_tag:
            date_str = date_tag.text.strip()
            for fmt in ("%B %d, %Y", "%b. %d, %Y", "%b %d, %Y"):
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.year, dt.month, dt.day, date_str
                except ValueError:
                    continue
    except Exception as e:
        print(f"❓ Failed to fetch or parse article date from {url}: {e}")
        return None

def scrape_sitemap_month(year, month, db):
    base_url = f"https://www.latimes.com/sitemap/{year}/{month}"
    subpages = ["", "/p/2", "/p/3"]
    seen = set()
    total_added = 0

    for sub in subpages:
        url = base_url + sub
        print(f"\n🔗 Fetching: {url}")

        try:
            html = fetch_page_source_with_browser(url)
            if not html:
                print(f"❌ Failed to fetch sitemap via browser: {url}")
                continue
        except Exception as e:
            print(f"❌ Error fetching sitemap: {e}")
            continue

        soup = BeautifulSoup(html, "html.parser")
        main = soup.find("main", class_="page-main")
        link_elements = main.find_all("a", href=True) if main else []

        print(f"🔍 Found {len(link_elements)} links on page.")

        added = 0
        for a in link_elements:
            href = a.get("href")
            print(f"🔗 Checking: {href}")
            if href in seen or not href or not href.startswith("https://www.latimes.com"):
                continue
            seen.add(href)

            if not is_allowed_section(href):
                print("⛔ Skipped due to disallowed section.")
                continue

            headline = a.get_text(strip=True)
            if not headline or len(headline) < 20:
                print("🧐 Skipped due to short or missing headline.")
                continue

            date_info = fetch_article_date(href)
            if not date_info:
                print("❓ Failed to extract publication date.")
                continue

            y, m, d, article_time = date_info

            entry = {
                'headline': headline,
                'article_time': article_time,
                'year': y,
                'month': m,
                'day': d,
                'keyword': 'latimes',
                'link': href,
                'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'scanned_status': 0
            }

            if db.insert(entry):
                print(f"✅ Inserted: {href}")
                added += 1

        print(f"📦 Added {added} articles for {year}-{month:02d} (Page {sub if sub else '1'})")
        total_added += added

    print(f"📦 Total articles added for {year}-{month:02d}: {total_added}")

def main():
    db = LATimesDB()

    for month in range(1, 13):
        scrape_sitemap_month(2024, month, db)

    db.close()
    print("\n🏁 Link scraping completed.")

if __name__ == "__main__":
    main()
