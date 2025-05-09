import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from datetime import datetime

# Database manager for inserting article links
class ManagementDB:
    def __init__(self, db_name):
        self.name = db_name
        self.conn = sqlite3.connect(self.name)
        self.c = self.conn.cursor()

    def insert_elements(self, elements):
        try:
            self.c.execute("""
                INSERT INTO articles_index 
                (headline, article_time, year, month, day, keyword, link, scraped_at, scanned_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                elements["headline"], elements["article_time"], elements["year"], elements["month"],
                elements["day"], elements["keyword"], elements["link"], elements["scraped_at"], elements["scanned_status"]
            ))
            self.conn.commit()
        except sqlite3.IntegrityError:
            # Ignore duplicates due to UNIQUE constraint on 'link'
            pass
        except sqlite3.Error as e:
            print(f"❌ DB error: {e}")

    def closeDB(self):
        self.conn.close()

# WSJ archive scraper for collecting article links per day
class WebScrap:
    def __init__(self, db_name):
        self.db_name = db_name
        self.page_number = 1

    def should_exclude_link(self, url):
        irrelevant_sections = [
            "/health/", "/arts-culture/", "/lifestyle/", "/real-estate/", "/sports/",
            "/livecoverage/", "/personal-finance/", "/video/", "/science/",
            "/style/", "/opinion/", "/articles/"
        ]
        return any(section in url for section in irrelevant_sections)


    def get_elements_for_day_filtered(self, year, month, day, max_articles=30, waiting_time=5):
        db = ManagementDB(self.db_name)
        collected = 0
        end_page = False
        self.page_number = 1

        # Fetch existing links to avoid duplicates
        db.c.execute("SELECT link FROM articles_index")
        seen_links = set(row[0] for row in db.c.fetchall())

        while not end_page and collected < max_articles:
            if self.page_number == 1:
                title_url = f'https://www.wsj.com/news/archive/{year}/{month:02d}/{day:02d}'
            else:
                title_url = f'https://www.wsj.com/news/archive/{year}/{month:02d}/{day:02d}?page={self.page_number}'

            print(f"🌐 {title_url}")

            headers = {'User-Agent': 'Mozilla/5.0'}
            page = requests.get(title_url, headers=headers)

            if page.status_code != 200:
                print(f"❌ Failed to load page: {title_url}")
                break

            soup = BeautifulSoup(page.content, 'html.parser')
            articles = soup.find_all('article')
            print(f"🔎 Found {len(articles)} <article> elements.")

            if not articles:
                print("❌ No articles found on page.")
                break

            for article in articles:
                if collected >= max_articles:
                    break

                a_tag = article.find('a', href=True)
                link = a_tag['href'] if a_tag else None
            
                if link in seen_links:
                    print(f"♻️ Skipped (already in DB): {link}")
                    continue

                if self.should_exclude_link(link):
                    print(f"❌ Excluded due to section: {link}")
                    continue


                headline_tag = article.find('span', class_='WSJTheme--headlineText--He1ANr9C')
                headline = headline_tag.text.strip() if headline_tag else "N/A"

                timestamp_tag = article.find('p', class_='WSJTheme--timestamp--22sfkNDv')
                timestamp = timestamp_tag.text.strip() if timestamp_tag else "N/A"

                # New structure: use the inner <div> instead of <span>
                type_div = article.find('div', class_='WSJTheme--articleType--34Gt-vdG')
                type_inner = type_div.find('div') if type_div else None
                keyword = type_inner.text.lower().strip() if type_inner and type_inner.text else "unknown"

                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                db.insert_elements({
                    'headline': headline,
                    'article_time': timestamp,
                    'year': year,
                    'month': month,
                    'day': day,
                    'keyword': keyword,
                    'link': link,
                    'scraped_at': current_time,
                    'scanned_status': 0
                })

                collected += 1
                seen_links.add(link)

            if collected < max_articles:
                self.page_number += 1
                time.sleep(waiting_time)
            else:
                end_page = True

        db.closeDB()
        print(f"✅ Collected {collected} articles for {year}-{month:02d}-{day:02d}")

