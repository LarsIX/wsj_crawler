import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from datetime import datetime, timedelta


ALLOWED_SECTIONS = {'business', 'opinion', 'world', 'us-news', 'tech', 'u.s.', 'finance', 'economy', 'politics', 'review-&-outlook', 'business-world'}


class ManagementDB:
    def __init__(self, db_name='articleswsj_2023.db'):
        self.conn = sqlite3.connect(db_name)
        self.c = self.conn.cursor()

    def insert_elements(self, elements):
        try:
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
            print(f"❌ Database Insert Error: {e}")

    def exploration(self, link, day, month, year, page_num, values_or_not, count_articles):
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.c.execute("""
                INSERT INTO exploration 
                (link, day, month, year, page_num, checked_at, values_or_not, count_articles)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (link, day, month, year, page_num, current_time, values_or_not, count_articles))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"❌ Exploration Logging Error: {e}")

    def link_exists(self, link):
        self.c.execute("SELECT 1 FROM articles_index WHERE link = ?", (link,))
        return self.c.fetchone() is not None

    def closeDB(self):
        self.conn.close()

class WebScrap:
    def __init__(self):
        self.page_number = 1
        self.total_articles = 0

    def reset(self):
        self.page_number = 1
        self.total_articles = 0

    def get_elements_from_web(self, year, month, day, waiting_time):
        db = ManagementDB()
        while True:
            if self.page_number == 1:
                url = f'https://www.wsj.com/news/archive/{year}/{month:02}/{day:02}'
            else:
                url = f'https://www.wsj.com/news/archive/{year}/{month:02}/{day:02}?page={self.page_number}'

            print(f"\n🔎 Scraping URL: {url}")

            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                print(f"❌ Failed to retrieve page. Status Code: {response.status_code}")
                break

            soup = BeautifulSoup(response.content, 'html.parser')
            ol_element = soup.find('ol', class_='WSJTheme--list-reset--3pR-r52l')
            article_elements = ol_element.find_all('article') if ol_element else []

            if not article_elements:
                db.exploration(url, day, month, year, self.page_number, 0, 0)
                print(f"✅ Finished scraping for {day}-{month}-{year}. Total articles: {self.total_articles}")
                break

            count_articles = 0

            for article in article_elements:
                headline_span = article.find('span', class_='WSJTheme--headlineText--He1ANr9C')
                a_tag = article.find('a')
                timestamp_p = article.find('p', class_='WSJTheme--timestamp--22sfkNDv')

                headline_text = headline_span.text if headline_span else "N/A"
                article_link = a_tag['href'] if a_tag else "N/A"
                article_time = timestamp_p.text if timestamp_p else "N/A"

                # Extract section directly from archive listing
                article_type_div = article.find('div', class_='WSJTheme--articleType--34Gt-vdG')
                section_div = article_type_div.find('div') if article_type_div else None
                article_section = section_div.text.strip().lower().replace(' ', '-') if section_div else "N/A"

                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                dict_elements = {
                    'headline': headline_text,
                    'article_time': article_time,
                    'year': year,
                    'month': month,
                    'day': day,
                    'keyword': article_section,
                    'link': article_link,
                    'scraped_at': current_time,
                    'scanned_status': 0,
                }

                if article_section in ALLOWED_SECTIONS and not db.link_exists(article_link):
                    db.insert_elements(dict_elements)
                    count_articles += 1

            db.exploration(url, day, month, year, self.page_number, 1, count_articles)
            self.total_articles += count_articles

            # Continue to next page regardless of article count
            self.page_number += 1
            time.sleep(waiting_time)

        db.closeDB()
        self.reset()

def get_dates(year):
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    return [[current_date.day, current_date.month, current_date.year] 
            for current_date in (start_date + timedelta(days=n) for n in range((end_date - start_date).days + 1))]

def searching(target_year, waiting_time):
    dates = get_dates(target_year)
    scraper = WebScrap()

    for day, month, year in dates:
        print(f"\n📅 Starting scrape for date: {day}-{month}-{year}")
        scraper.get_elements_from_web(year, month, day, waiting_time)
        time.sleep(waiting_time)

if __name__ == '__main__':
    year_to_scrape = 2023     # Year to scrape
    waiting_time = 7          # Time to wait between requests (seconds)

    searching(year_to_scrape, waiting_time)
    print("\n🏁 Scraping completed successfully.")
