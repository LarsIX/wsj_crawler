import os
import time
import random
import sqlite3
from datetime import datetime
import numpy as np
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

class Search4Articles:
    def __init__(self, db_name='articlesWSJ.db'):
        self.url = "https://www.wsj.com/"
        self.db_name = db_name

        self.user_data_dir = "C:/Users/PC/AppData/Local/Google/Chrome/User Data"
        self.profile_dir = "Profile 1"

        self.driver = self.create_driver()
        self.link_index = 7

    def create_driver(self):
        options = uc.ChromeOptions()
        options.add_argument(f"--user-data-dir={self.user_data_dir}")
        options.add_argument(f"--profile-directory={self.profile_dir}")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        driver = uc.Chrome(options=options)
        driver.get(self.url)
        return driver

    def get_webpages_links(self, n_web):
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        c.execute("SELECT * FROM articles_index WHERE scanned_status = 0")
        rows = c.fetchall()
        conn.close()

        if rows and len(rows) >= n_web:
            links = np.array([[row[0], row[self.link_index]] for row in rows])
            pp = np.random.choice(len(rows), n_web, replace=False)
            return links[pp]
        else:
            return []

    def should_exclude_link(self, url):
        exclude_keywords = [
            "health", "arts-culture", "lifestyle", "real-estate", "sports", 
            "livecoverage", "personal-finance", "video", "science", 
            "style", "articles", "opinion"
        ]
        return any(f"/{keyword}/" in url or url.startswith(f"https://www.wsj.com/{keyword}") for keyword in exclude_keywords)

    def get_corpus(self):
        try:
            h1 = self.driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
        except NoSuchElementException:
            h1 = ''

        try:
            h2 = self.driver.find_element(By.CSS_SELECTOR, "h2").text.strip()
        except NoSuchElementException:
            h2 = ''

        possible_sections = [
            "section.ef4qpkp0.css-y2scx8-Container.e1of74uw18",
            "div.article-content",
            "section",
            "main"
        ]

        content = ''
        for selector in possible_sections:
            try:
                container = self.driver.find_element(By.CSS_SELECTOR, selector)
                text = container.text.strip()
                if len(text) > len(content):
                    content = text
            except NoSuchElementException:
                continue

        return h1, h2, content

    def insert_elements(self, elements):
        if not elements['corpus'] or elements['corpus'] == 'not found':
            print(f"⚠️ No valid content – Skipping article {elements['index_id']}.")
            return

        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO article 
                (image_src, scanned_time, title, sub_title, corpus, index_id) 
                VALUES (?, ?, ?, ?, ?, ?)""",
                ('', elements['scanned_time'], elements['title'],
                elements['sub_title'], elements['corpus'], elements['index_id']))
            cursor.execute("UPDATE articles_index SET scanned_status = 1 WHERE id = ?", (elements['index_id'],))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def navigation(self, max_per_day=30, year=None, month=None, day=None):
        if year is not None and month is not None and day is not None:
            dates = [(year, month, day)]
        else:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("""
                SELECT DISTINCT year, month, day
                FROM articles_index
                WHERE scanned_status = 0
                ORDER BY year, month, day
            """)
            dates = c.fetchall()
            conn.close()

        for y, m, d in dates:
            ymd = f"{int(y)}-{int(m):02d}-{int(d):02d}"
            print(f"\n📆 {ymd}: Scraping up to {max_per_day} articles")

            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("""
                SELECT COUNT(DISTINCT a.article_id)
                FROM article a
                JOIN articles_index ai ON ai.id = a.index_id
                WHERE ai.year = ? AND ai.month = ? AND ai.day = ?
                AND a.corpus IS NOT NULL 
                AND a.corpus != '' 
                AND a.corpus != 'not found'
            """, (y, m, d))
            count_existing = c.fetchone()[0]
            conn.close()

            print(f"🔍 DB says we have {count_existing} valid articles for {ymd}")

            if count_existing >= max_per_day:
                print(f"✅ Already have {count_existing} articles – skipping.")
                continue

            remaining = max_per_day - count_existing

            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("""
                SELECT id, link
                FROM articles_index
                WHERE scanned_status = 0 AND year = ? AND month = ? AND day = ?
                LIMIT ?
            """, (y, m, d, remaining))
            rows = c.fetchall()
            conn.close()

            if not rows:
                print("⚠️ No unscanned articles for this day.")
                continue

            for idx, link in rows:
                if self.should_exclude_link(link):
                    print(f"⛔ Skipping article {idx} from excluded category.")
                    continue

                print(f"➡️ Opening article {idx}: {link}")
                self.driver.get(link)
                time.sleep(random.uniform(3, 7))

                h1, h2, content = self.get_corpus()
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                self.insert_elements({
                    'scanned_time': now,
                    'title': h1,
                    'sub_title': h2,
                    'corpus': content,
                    'index_id': idx
                })

                print("✅ Article saved\n")
                time.sleep(random.uniform(2, 5))
