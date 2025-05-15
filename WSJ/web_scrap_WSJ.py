import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import sqlite3
from datetime import datetime

class WSJScraper:
    def __init__(self, db_path):
        self.db_path = db_path
        self.url = "https://www.wsj.com/"
        self.driver = self.create_driver()
    
    def create_driver(self):
        options = Options()
        options.debugger_address = "127.0.0.1:9222"  # remote access to Chrome
        driver = webdriver.Chrome(options=options)
        driver.get(self.url)
        time.sleep(5)  # wait for the page to load
        return driver

    # handle cookie banner
    def close_cookie_banner(self):
        try:
            btn = self.driver.find_element(By.CSS_SELECTOR, "button.agree-btn[title='YES, I AGREE']")
            btn.click()
            print("🍪 Cookie-Banner accepted")
            time.sleep(2)
        except NoSuchElementException:
            print("ℹ️ No Cookie-Banner found.")
    
    # get article links from the database
    def get_article_links(self, limit=30, year=None, month=None, day=None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if year and month and day:
            c.execute("""
                SELECT id, link FROM articles_index
                WHERE scanned_status = 0 AND year=? AND month=? AND day=?
                LIMIT ?
            """, (year, month, day, limit))
        else:
            c.execute("""
                SELECT id, link FROM articles_index
                WHERE scanned_status = 0
                LIMIT ?
            """, (limit,))
        
        rows = c.fetchall()
        conn.close()
        return rows

    # scrape article
    def scrape_article(self, article_id, url):
        print(f"➡️ open article {article_id}: {url}")
        self.driver.get(url)
        time.sleep(5)
        self.close_cookie_banner()

        # load header
        try:
            title = self.driver.find_element(By.CSS_SELECTOR, "h1").text.strip()
        except NoSuchElementException:
            title = ""

        # load subheader
        try:
            subtitle = self.driver.find_element(By.CSS_SELECTOR, "h2").text.strip()
        except NoSuchElementException:
            subtitle = ""

        # load corpus
        content = ""
        selectors = [
            "section.ef4qpkp0.css-y2scx8-Container.e1of74uw18",
            "div.article-content",
            "section",
            "main"
        ]

        for sel in selectors:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, sel)
                text = el.text.strip()
                if len(text) > len(content):
                    content = text
            except NoSuchElementException:
                continue
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not content:
            print(f"⚠️ No text found in {article_id}, skipping...")
            return

        # safe to db
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                INSERT INTO article (image_src, scanned_time, title, sub_title, corpus, index_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, ('', now, title, subtitle, content, article_id))
            c.execute("UPDATE articles_index SET scanned_status=1 WHERE id=?", (article_id,))
            conn.commit()
            conn.close()
            print(f"✅ Artikel {article_id} gespeichert.")
        except sqlite3.Error as e:
            print(f"❌ DB Error at article {article_id}: {e}")

    def close(self):
        self.driver.quit()
