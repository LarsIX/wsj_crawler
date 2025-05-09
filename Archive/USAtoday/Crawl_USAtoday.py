import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime

DB_PATH = r"C:\Users\PC\Desktop\Masterarbeit\Code\USAtoday\articlesUSAToday.db"

class USATodayDB:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()

    def insert(self, entry):
        self.c.execute("SELECT 1 FROM articles_index WHERE link = ?", (entry["link"],))
        if self.c.fetchone():
            print(f"⚠️ Bereits vorhanden: {entry['link']}")
            return False

        self.c.execute("""
            INSERT INTO articles_index 
            (headline, article_time, year, month, day, keyword, link, scraped_at, scanned_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry["headline"], entry["article_time"], entry["year"], entry["month"], entry["day"],
            entry["keyword"], entry["link"], entry["scraped_at"], entry["scanned_status"]
        ))
        self.conn.commit()
        return True

    def close(self):
        self.conn.close()

def scrape_sitemap_for_day(year, month, day, db, max_articles=30):
    month_names = [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"
    ]
    month_str = month_names[month - 1]
    url = f"https://eu.usatoday.com/sitemap/{year}/{month_str}/{day:02d}/"
    print(f"\n🔗 {url}")

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"❌ Fehler beim Abrufen der Sitemap ({response.status_code})")
            return
    except Exception as e:
        print(f"❌ Anfragefehler: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("li", class_="sitemap-list-item")

    added = 0
    seen = set()

    excluded_patterns = [
        "/videos", "/story/sports/", "/story/money/lottery", "/entertainment/", "/travel/", "/life/"
    ]

    for li in links:
        a = li.find("a", href=True)
        if not a:
            continue

        href = a["href"]
        if not href.startswith("https://www.usatoday.com/story/"):
            continue
        if any(excl in href for excl in excluded_patterns):
            continue
        if href in seen:
            continue
        seen.add(href)

        headline = a.get_text(strip=True)
        if not headline or len(headline) < 20:
            continue

        entry = {
            'headline': headline,
            'article_time': 'N/A',
            'year': year,
            'month': month,
            'day': day,
            'keyword': 'usatoday',
            'link': href,
            'scraped_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'scanned_status': 0
        }

        if db.insert(entry):
            print(f"✅ Eingefügt: {href}")
            added += 1

        if added >= max_articles:
            break

def main():
    db = USATodayDB()

    for month in range(1, 13):
        for day in range(1, 32):
            try:
                datetime(2024, month, day)  # valid date check
                scrape_sitemap_for_day(2024, month, day, db, max_articles=30)
            except ValueError:
                continue

    db.close()
    print("\n🏁 Link-Scraping abgeschlossen.")

if __name__ == "__main__":
    main()
