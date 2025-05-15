import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import sqlite3
import time

# Database management class
class ManagementDB():
    def __init__(self, db_name='articlesWSJ.db'):
        self.name = db_name
        self.conn = sqlite3.connect(self.name)
        self.c = self.conn.cursor()

    # Insert a new article entry into the articles_index table
    def insert_elements(self, elements):
        try:
            self.c.execute("""
                INSERT INTO articles_index (headline, article_time, year, month, day, keyword, link, scraped_at, scanned_status) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                elements["headline"], elements["article_time"], elements["year"], elements["month"], 
                elements["day"], elements["keyword"], elements["link"], elements["scraped_at"], 
                elements["scanned_status"]
            ))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")

    # Log exploration attempts into the exploration table
    def exploration(self, link, day, month, year, page_num, values_or_not, count_articles):
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.c.execute("""
                INSERT INTO exploration (link, day, month, year, page_num, checked_at, values_or_not, count_articles) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (link, day, month, year, page_num, current_time, values_or_not, count_articles))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"An error occurred: {e}")

    def closeDB(self):
        self.conn.close()

# Web crawler for collecting WSJ article metadata
class WebCrawl:
    def __init__(self):
        self.page_number = 1
        self.total_articles = 0

    def reset(self):
        # Reset counters after finishing a day or hitting an end page
        self.page_number = 1
        self.total_articles = 0

    # Save collected articles metadata to JSON for backup
    def _save_to_json(self, article_details, year, month, day):
        title_json = f"article_titles_json/index_{year}_{month}_{day}_page_{self.page_number}.json"
        with open(title_json, 'w') as f:
            json.dump(article_details, f)
        print(f'📁 Article details saved to {title_json}')

    # Main method to collect article metadata for a given day
    def get_elements_from_web(self, year, month, day, waiting_time):
        db = ManagementDB()
        end_page = False

        while not end_page:
            # Handle correct URL structure for pagination
            title_url = f'https://www.wsj.com/news/archive/{year}/{month:02d}/{day:02d}'
            if self.page_number > 1:
                title_url += f"?page={self.page_number}"

            print(f"🌐 Visiting: {title_url}")

            headers = {'User-Agent': 'Mozilla/5.0'}
            page = requests.get(title_url, headers=headers)

            if page.status_code != 200:
                print(f"❌ Failed to retrieve the page. Status code: {page.status_code}")
                end_page = True
                self.reset()
                continue

            soup = BeautifulSoup(page.content, 'html.parser')
            ol_element = soup.find('ol', class_='WSJTheme--list-reset--3pR-r52l')

            if not ol_element:
                print("⚠️ No article list found on this page.")
                end_page = True
                self.reset()
                continue

            article_elements = ol_element.find_all('article')

            if not article_elements:
                # Log empty page exploration and exit
                db.exploration(title_url, day, month, year, self.page_number, 0, 0)
                end_page = True
                self.reset()
                continue

            count_articles = 0
            article_details = []

            for article in article_elements:
                # Extract metadata
                headline_span = article.find('span', class_='WSJTheme--headlineText--He1ANr9C')
                a_tag = article.find('a')
                timestamp_p = article.find('p', class_='WSJTheme--timestamp--22sfkNDv')

                headline_text = headline_span.text if headline_span else "N/A"
                article_link = a_tag['href'] if a_tag else "N/A"
                article_time = timestamp_p.text if timestamp_p else "N/A"

                # Extract article type/section
                article_type_div = article.find('div', class_='WSJTheme--articleType--34Gt-vdG')
                empty_class_span = article_type_div.find('span', class_='') if article_type_div else None
                article_type_text = empty_class_span.text if empty_class_span else "N/A"

                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Build dictionary for this article's metadata
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

                # Save to DB
                db.insert_elements(dict_elements)

                count_articles += 1

            # Save results to JSON backup
            self._save_to_json(article_details, year, month, day)

            # Log the successful exploration attempt
            db.exploration(title_url, day, month, year, self.page_number, 1, count_articles)

            self.total_articles += count_articles

            # Decide whether to continue to the next page or finish
            if count_articles == 50:
                self.page_number += 1
                time.sleep(waiting_time)
            else:
                print(f"✅ Articles collected for the day: {self.total_articles}")
                end_page = True
                self.reset()

        db.closeDB()

# Generate all dates for a given year
def get_dates(year):
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    date_list = []

    current_date = start_date
    while current_date <= end_date:
        date_list.append([current_date.day, current_date.month, current_date.year])
        current_date += timedelta(days=1)

    return date_list

# Entry point for scraping a full year
def searching(year, waiting_time):
    dates = get_dates(year)
    scrap = WebCrawl()
    for day, month, year in dates:
        print(f"📅 Processing: {day}-{month}-{year}")
        scrap.get_elements_from_web(year, month, day, waiting_time)
        time.sleep(waiting_time)

if __name__ == '__main__':
    # Configuration for scraping year and waiting time between requests
    year = 2024
    waiting_time = 7  # Seconds between page loads

    searching(year, waiting_time)
    print("🏁 Done collecting metadata.")
