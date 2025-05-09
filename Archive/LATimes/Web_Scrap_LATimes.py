import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime

DB_PATH = r"C:\Users\PC\Desktop\Masterarbeit\Code\LATimes\articlesLAT.db"

def extract_article_body_and_title(html):
    soup = BeautifulSoup(html, "html.parser")

    # Find main body
    story_body = soup.find("div", attrs={"data-element": "story-body"})
    if not story_body:
        print("❌ No story body div found.")
        return None, None

    paragraphs = story_body.find_all("p")
    text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

    # Extract title from h1.headline
    title_tag = soup.find("h1", class_="headline")
    title = title_tag.get_text(strip=True) if title_tag else None
    if not title:
        print("⚠️ No title found.")

    return text if text else None, title

class LATimesDownloader:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()

    def fetch_unscraped_articles(self):
        self.c.execute("SELECT id, link FROM articles_index WHERE scanned_status = 0")
        return self.c.fetchall()

    def mark_as_scraped(self, index_id):
        self.c.execute("UPDATE articles_index SET scanned_status = 1 WHERE id = ?", (index_id,))
        self.conn.commit()

    def save_article(self, index_id, text, title):
        scanned_time = datetime.now().isoformat()
        self.c.execute('''
            INSERT INTO article (image_src, scanned_time, title, sub_title, corpus, index_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ("", scanned_time, title, "", text, index_id))
        self.conn.commit()

    def run(self):
        entries = self.fetch_unscraped_articles()
        print(f"📝 {len(entries)} articles to process.\n")

        for idx, (index_id, link) in enumerate(entries, start=1):
            print(f"📄 ({idx}/{len(entries)}) Fetching: {link}")
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
                }
                res = requests.get(link, headers=headers, timeout=10)
                res.raise_for_status()

                text, title = extract_article_body_and_title(res.text)
                if not text:
                    print(f"❌ No article body found: {link}\n")
                    continue

                self.save_article(index_id, text, title)
                self.mark_as_scraped(index_id)
                print(f"✅ Successfully saved: {link}\n")

            except Exception as e:
                print(f"❗ Error processing {link}: {e}\n")

        print("🏁 Article content download completed.")

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    downloader = LATimesDownloader()
    downloader.run()
    downloader.close()
    print("🗄️ Database connection closed.")