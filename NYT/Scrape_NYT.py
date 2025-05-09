import os
import time
import random
import sqlite3
from datetime import datetime
import numpy as np
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import logging


logging.basicConfig(level=logging.INFO)

class SearchNYTArticles:
    def __init__(self, db_name=r"C:\Users\PC\Desktop\Masterarbeit\Code\NYT\articlesNYT.db"):
        print("🔧 Initialisiere Scraper")
        self.url = "https://www.nytimes.com/"
        self.db_name = db_name

        self.user_data_dir = "C:/Users/PC/AppData/Local/Google/Chrome/User Data"
        self.profile_dir = "Profile 1"

        print("🛠️ Create Driver")
        self.driver = self.create_driver()
        print("🚀 Driver created")

        self.link_index = 7

    def create_driver(self):
        print("⚙️ Starte Chrome mit Profil...")
        options = uc.ChromeOptions()
        options.add_argument(f"--user-data-dir={self.user_data_dir}")
        options.add_argument(f"--profile-directory={self.profile_dir}")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")

        driver = uc.Chrome(options=options)
        print("🌍 Navigiere zu Startseite...")
        driver.get(self.url)
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

        possible_sections = [
            "section[name='articleBody']",
            "section[data-testid='article-summary']",
            "section",
            "main",
            "article"
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
            print(f"⚠️ Kein brauchbarer Inhalt – Artikel {elements['index_id']} wird übersprungen.")
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
            print(f"DB-Fehler: {e}")

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
            ymd = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"

            print(f"\n📆 {ymd}: max. {max_per_day} Article")

            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("""
                SELECT COUNT(*) 
                FROM article a
                JOIN articles_index ai ON ai.id = a.index_id
                WHERE ai.year = ? AND ai.month = ? AND ai.day = ?
                AND a.corpus IS NOT NULL 
                AND a.corpus != '' 
                AND a.corpus != 'not found'
            """, (y, m, d))
            count_existing = c.fetchone()[0]
            conn.close()

            if count_existing >= max_per_day:
                print(f"✅ Schon {count_existing} Artikel vorhanden – überspringe.")
                continue

            remaining = max_per_day - count_existing

            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute("""
                SELECT id, link
                FROM articles_index
                WHERE scanned_status = 0 AND year = ? AND month = ? AND day = ?
                AND link LIKE '%nytimes.com%'
                LIMIT ?
            """, (y, m, d, remaining))
            rows = c.fetchall()
            conn.close()

            if not rows:
                print("⚠️ Keine ungescannten Artikel für diesen Tag.")
                continue

            for idx, link in rows:
                print(f"➡️ Öffne Artikel {idx}: {link}")
                try:
                    self.driver.get(link)
                    time.sleep(random.uniform(4, 7))
                except Exception as e:
                    print(f"❌ Fehler beim Öffnen von {link}: {e}")
                    continue

                try:
                    h1, h2, content = self.get_corpus()
                    print(f"📰 H1: {h1[:60]}...")
                    print(f"📄 Corpus-Länge: {len(content)}")
                except Exception as e:
                    print(f"❌ Fehler beim Extrahieren des Inhalts: {e}")
                    continue

                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                try:
                    self.insert_elements({
                        'scanned_time': now,
                        'title': h1,
                        'sub_title': h2,
                        'corpus': content,
                        'index_id': idx
                    })
                    print("✅ Artikel gespeichert\n")
                except Exception as e:
                    print(f"❌ Fehler beim Speichern in DB: {e}")

                time.sleep(random.uniform(4, 9))

if __name__ == '__main__':
    scanner = SearchNYTArticles()
    scanner.navigation(max_per_day=30)
