import time
import random
import sqlite3
from datetime import datetime
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

DB_PATH = r"C:\Users\PC\Desktop\Masterarbeit\Code\USAtoday\articlesUSAToday.db"

class ScrapeUSATodayContent:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.user_data_dir = "C:/Users/PC/AppData/Local/Google/Chrome/User Data"
        self.profile_dir = "Profile 1"
        self.driver = self.create_driver()

    def create_driver(self):
        options = uc.ChromeOptions()
        options.add_argument(f"--user-data-dir={self.user_data_dir}")
        options.add_argument(f"--profile-directory={self.profile_dir}")
        options.add_argument("--start-maximized")
        driver = uc.Chrome(options=options)
        return driver

    def get_corpus(self):
        try:
            h1 = self.driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
        except NoSuchElementException:
            h1 = ''

        try:
            h2 = self.driver.find_element(By.CSS_SELECTOR, "h2").text.strip()
        except NoSuchElementException:
            h2 = ''

        content = ''
        possible_containers = [
            "div.gnt_ar_b",  # main body class on usatoday
            "div.gnt_ar_t",  # fallback
            "article",       # general fallback
        ]

        for selector in possible_containers:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, selector)
                text = el.text.strip()
                if len(text) > len(content):
                    content = text
            except NoSuchElementException:
                continue

        return h1, h2, content

    def insert_article(self, data):
        if not data['corpus'] or data['corpus'] == 'not found':
            print(f"⚠️ Kein Inhalt – Artikel {data['index_id']} wird übersprungen.")
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''INSERT INTO article 
            (image_src, scanned_time, title, sub_title, corpus, index_id)
            VALUES (?, ?, ?, ?, ?, ?)''',
            ('', data['scanned_time'], data['title'], data['sub_title'], data['corpus'], data['index_id']))

        c.execute("UPDATE articles_index SET scanned_status = 1 WHERE id = ?", (data['index_id'],))
        conn.commit()
        conn.close()

    def scrape_pending_articles(self, max_per_day=30):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            SELECT DISTINCT year, month, day FROM articles_index
            WHERE scanned_status = 0
            ORDER BY year, month, day
        """)
        dates = c.fetchall()
        conn.close()

        for y, m, d in dates:
            print(f"\n📅 {y}-{int(m):02d}-{int(d):02d}")

            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                SELECT id, link FROM articles_index
                WHERE scanned_status = 0 AND year = ? AND month = ? AND day = ?
                LIMIT ?
            """, (y, m, d, max_per_day))
            rows = c.fetchall()
            conn.close()

            for idx, link in rows:
                print(f"➡️ Öffne Artikel {idx}: {link}")
                try:
                    self.driver.get(link)
                    time.sleep(random.uniform(4, 7))
                    h1, h2, content = self.get_corpus()
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    self.insert_article({
                        'scanned_time': now,
                        'title': h1,
                        'sub_title': h2,
                        'corpus': content,
                        'index_id': idx
                    })

                    print("✅ Gespeichert\n")
                    time.sleep(random.uniform(4, 8))
                except Exception as e:
                    print(f"❌ Fehler bei Artikel {idx}: {e}")

        self.driver.quit()
        print("\n🏁 Inhalts-Scraping abgeschlossen.")

if __name__ == '__main__':
    scraper = ScrapeUSATodayContent()
    scraper.scrape_pending_articles(max_per_day=30)
