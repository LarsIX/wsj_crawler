import os
import sqlite3
import time
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Path to the SQLite database
DB_PATH = r"C:\Users\PC\Desktop\Masterarbeit\Code\NYT\articlesNYT.db"

# Handles database operations
class ManagementNYT:
    def __init__(self, db_name=DB_PATH):
        self.name = db_name
        self.conn = sqlite3.connect(self.name)
        self.c = self.conn.cursor()

    def insert_elements(self, elements):
        try:
            # Avoid duplicates
            self.c.execute("SELECT 1 FROM articles_index WHERE link = ?", (elements["link"],))
            if self.c.fetchone():
                print(f"⚠️ Link already exists – skipping: {elements['link']}")
                return

            # Insert new article entry
            self.c.execute("""
                INSERT INTO articles_index 
                (headline, article_time, year, month, day, keyword, link, scraped_at, scanned_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                elements["headline"], elements["article_time"], elements["year"], elements["month"], elements["day"],
                elements["keyword"], elements["link"], elements["scraped_at"], elements["scanned_status"]
            ))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"❌ DB Insert Error: {e}")

    def closeDB(self):
        self.conn.close()

# Scrapes article links from NYT Today's Paper
class WebScrapNYT:
    def __init__(self):
        self.total_articles = 0
        self.user_data_dir = "C:/Users/PC/AppData/Local/Google/Chrome/User Data"
        self.profile_dir = "Profile 1"

        options = Options()
        options.add_argument(f"user-data-dir={self.user_data_dir}")
        options.add_argument(f"profile-directory={self.profile_dir}")
        options.add_argument("--headless=new")  # Headless browsing (you can remove this if you want to see the browser)
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        self.driver = webdriver.Chrome(options=options)

    def get_elements_from_web(self, year, month, day, max_articles=30, wait_time=5):
        url = f"https://www.nytimes.com/issue/todayspaper/{year}/{month:02d}/{day:02d}/todays-new-york-times"
        print(f"🔗 {url}")

        try:
            self.driver.get(url)
            time.sleep(5)  # Give the page time to load fully

            soup = BeautifulSoup(self.driver.page_source, "lxml")
            article_blocks = soup.find_all("li", class_="css-i435f0")

            db = ManagementNYT()
            added = 0
            print(f"🔍 Found {len(article_blocks)} article containers")

            for block in article_blocks:
                a_tag = block.find("a", href=True)
                headline_tag = block.find("h2", class_="css-qvuipm")

                if not a_tag or not headline_tag:
                    print("⚠️ Missing headline or link – skipping")
                    continue

                href = a_tag["href"]
                title = headline_tag.get_text(strip=True)

                if not title or " " not in title:
                    print("⚠️ Invalid title – skipping")
                    continue
                if not href.startswith("http"):
                    href = "https://www.nytimes.com" + href

                entry = {
                    'headline': title,
                    'article_time': "N/A",
                    'year': year,
                    'month': month,
                    'day': day,
                    'keyword': "N/A",
                    'link': href,
                    'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'scanned_status': 0
                }

                db.insert_elements(entry)
                added += 1
                print("✅ Article added:", title)

                if added >= max_articles:
                    break

            db.closeDB()
            print(f"📄 Total articles saved: {added}")
            time.sleep(wait_time)
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")

    def close(self):
        self.driver.quit()

# Generates all days of a given year
def get_dates(year):
    start = datetime(year, 1, 1)
    end = datetime(year, 12, 31)
    return [(d.day, d.month, d.year) for d in (start + timedelta(n) for n in range((end - start).days + 1))]

# Main loop over all dates
def searching(year, wait):
    ws = WebScrapNYT()
    for day, month, year in get_dates(year):
        ws.get_elements_from_web(year, month, day, max_articles=30, wait_time=wait)
    ws.close()

if __name__ == '__main__':
    searching(2024, wait=5)
    print("🏁 Finished crawling all NYT links for 2024.")