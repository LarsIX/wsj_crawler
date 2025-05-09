import os
import requests
from bs4 import BeautifulSoup
import json
import sqlite3
import time
from datetime import datetime, timedelta

class ManagementDB:
    def __init__(self, db_name):
        """
        Initialize a connection to the SQLite database.
        :param db_name: Full path to the database file.
        """
        self.name = db_name
        try:
            self.conn = sqlite3.connect(self.name)
            self.c = self.conn.cursor()
            print(f"✅ Connected to database: {self.name}")
        except sqlite3.Error as e:
            print(f"❌ Failed to connect to database: {e}")

    def insert_elements(self, elements):
        """
        Insert article metadata into articles_index.
        Skips if entry with same link already exists (optional safety).
        """
        try:
            self.c.execute("SELECT 1 FROM articles_index WHERE link = ?", (elements["link"],))
            if self.c.fetchone():
                print(f"⚠️ Link already exists – skipping: {elements['link']}")
                return

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
            print(f"❌ Error inserting element: {e}")

    def exploration(self, link, day, month, year, page_num, values_or_not, count_articles):
        """
        Log exploration activity in separate table for transparency/debugging.
        """
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.c.execute("""
                INSERT INTO exploration 
                (link, day, month, year, page_num, checked_at, values_or_not, count_articles)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (link, day, month, year, page_num, current_time, values_or_not, count_articles))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"❌ Error logging exploration: {e}")

    def closeDB(self):
        """
        Close the DB connection properly.
        """
        try:
            self.conn.close()
            print(f"🔐 Connection to database {self.name} closed.")
        except sqlite3.Error as e:
            print(f"❌ Error closing database: {e}")

class WebScrap:
    def __init__(self, db_name):
        self.db_name = db_name
        self.page_number = 1
        self.total_articles = 0

    def reset(self):
        self.page_number = 1
        self.total_articles = 0

    def _save_to_json(self, article_details, year, month, day):
        output_dir = "article_titles_json"
        os.makedirs(output_dir, exist_ok=True)

        title_json = os.path.join(output_dir, f"index_{year}_{month}_{day}_page_{self.page_number}.json")
        with open(title_json, 'w', encoding='utf-8') as f:
            json.dump(article_details, f, ensure_ascii=False, indent=2)
        print(f'✅ JSON saved to {title_json}')

    def get_elements_from_web(self, year, month, day, waiting_time):
        db = ManagementDB(db_name=self.db_name)
        end_page = False

        while not end_page:
            title_url = f'https://www.wsj.com/news/archive/{year}/{month}/{day}?page={self.page_number}'
            print(title_url)

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT x.y; Win64; x64; rv:10.0) Gecko/20100101 Firefox/10.0'
            }

            page = requests.get(title_url, headers=headers)
            article_details = []

            if page.status_code == 200:
                soup = BeautifulSoup(page.content, 'html.parser')
                print('Page status code:', page.status_code)

                ol_element = soup.find('ol', class_='WSJTheme--list-reset--3pR-r52l')

                if ol_element:
                    article_elements = ol_element.find_all('article')

                    if not article_elements:
                        db.exploration(title_url, day, month, year, self.page_number, 0, 0)
                        end_page = True
                        self.reset()
                    else:
                        count_articles = 0

                        for article in article_elements:
                            headline_span = article.find('span', class_='WSJTheme--headlineText--He1ANr9C')
                            a_tag = article.find('a')
                            timestamp_p = article.find('p', class_='WSJTheme--timestamp--22sfkNDv')

                            headline_text = headline_span.text if headline_span else "N/A"
                            article_link = a_tag['href'] if a_tag else "N/A"
                            article_time = timestamp_p.text if timestamp_p else "N/A"

                            article_type_div = article.find('div', class_='WSJTheme--articleType--34Gt-vdG')
                            empty_class_span = article_type_div.find('span', class_='') if article_type_div else None
                            article_type_text = empty_class_span.text if empty_class_span else "N/A"

                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                            dict_elements = {
                                'headline': headline_text,
                                'article_time': article_time,
                                'year': year,
                                'month': month,
                                'day': day,
                                'keyword': article_type_text,
                                'link': article_link,
                                'scraped_at': current_time,
                                'scanned_status': 0,
                            }

                            article_details.append(dict_elements)
                            db.insert_elements(dict_elements)
                            count_articles += 1

                        self._save_to_json(article_details, year, month, day)

                        db.exploration(title_url, day, month, year, self.page_number, 1, count_articles)
                        self.total_articles += count_articles

                        if count_articles == 50:
                            self.page_number += 1
                            time.sleep(waiting_time)
                        else:
                            print(f'Articles collected for {day:02d}.{month:02d}.{year}: {self.total_articles}')
                            end_page = True
                            self.reset()
                else:
                    print("⚠️ Could not find article list <ol> element.")
                    end_page = True
                    self.reset()
            else:
                print(f"❌ Failed to retrieve the page. Status code: {page.status_code}")
                end_page = True
                self.reset()

        db.closeDB()
