# 📰 WSJ Article Scraper & Cleaner (2024)

A complete pipeline for crawling, scraping, cleaning, and analyzing Wall Street Journal (WSJ) articles, designed for reproducible financial research and AI-related narrative analysis.

---

## 📂 Project Structure

```
├── create_DB.py
├── text_cleaner_WSJ.py
├── mentions_ai.py
├── web_scrap_WSJ.py
├── clean_database_WSJ_final.py
├── /2024
│   ├── main_2024.py
│   ├── crawl_WSJ_2024.py
│   ├── clean_database_WSJ_2024.ipynb   (Legacy Cleaner)
│   └── exploratory_analysis_wsj_2024.ipynb
└── README.md
```

---

## 🚀 Code Modules

### 🗂️ General Repository Files

#### `create_DB.py`
- Initializes SQLite databases with the correct schema for `articles_index`, `article`, and `exploration` tables.

#### `web_scrap_WSJ.py`
- Scrapes full article content from the WSJ archive based on metadata.
- Requires manual Chrome start with remote debugging (`--remote-debugging-port=9222`).

#### `text_cleaner_WSJ.py`
- Contains the `clean_article_text` function for preprocessing and cleaning article content.

#### `mentions_ai.py`
- Provides `flag_ai_mentions` function to flag AI-related content in articles.

#### `clean_database_WSJ_final.py`
- Final cleaner script to process raw databases into cleaned datasets.
- Handles duplicate removal, content cleaning, and creates a consolidated `date` column.

---

### 📅 2024 Folder Files

#### `main_2024.py`
- Orchestrates the 2024 scraping pipeline.
- Calls:
  - `crawl_WSJ_2024.WebCrawl` for metadata crawling.
  - `web_scrap_WSJ.WSJScraper` for full content scraping.
- Supports optional limit of **30 articles per day** for efficiency.

#### `crawl_WSJ_2024.py`
- Crawls WSJ archive for article metadata.
- Stores metadata in `articles_index` and logs exploration in `exploration`.

#### `clean_database_WSJ_2024.ipynb` *(Legacy Cleaner)*
- Early version cleaner. Kept for reproducibility but replaced by `clean_database_WSJ_final.py`.

#### `exploratory_analysis_wsj_2024.ipynb`
- Loads cleaned articles and performs exploratory analysis.
- Flags AI-related content and produces summary visualizations.

---

## 🗃️ Database Schema for articlesWSJ_<year>.db

### Table: `articles_index`

| Column        | Type    | Description          |
|----------------|---------|----------------------|
| `id`           | INTEGER | Primary Key          |
| `year`         | TEXT    | Year of publication  |
| `month`        | TEXT    | Month of publication |
| `day`          | TEXT    | Day of publication   |
| `headline`     | TEXT    | Article headline     |
| `article_time` | TEXT    | Time of publication  |
| `keyword`      | TEXT    | Keywords assigned    |
| `link`         | TEXT    | Article URL          |
| `scraped_at`   | TEXT    | Scraping timestamp   |
| `scanned_status` | INTEGER | 0 = Not Scanned, 1 = Scanned |

---

### Table: `article`

| Column        | Type    | Description        |
|----------------|---------|--------------------|
| `article_id`   | INTEGER | Primary Key        |
| `image_src`    | TEXT    | Article image URL  |
| `scanned_time` | TEXT    | Time of scraping   |
| `title`        | TEXT    | Article title      |
| `sub_title`    | TEXT    | Article subtitle   |
| `corpus`       | TEXT    | Full article text  |
| `index_id`     | INTEGER | Foreign Key → `articles_index.id` |

---

### Table: `exploration`

| Column        | Type    | Description          |
|----------------|---------|----------------------|
| `id`           | INTEGER | Primary Key          |
| `link`         | TEXT    | Explored URL         |
| `year`         | TEXT    | Exploration year     |
| `month`        | TEXT    | Exploration month    |
| `day`          | TEXT    | Exploration day      |
| `page_num`     | TEXT    | Page number explored |
| `checked_at`   | TEXT    | Timestamp checked    |
| `values_or_not`| INTEGER | 0 = No Articles, 1 = Articles Found |
| `count_articles` | INTEGER | Number of articles found |

---
## 🗃️ Database Schema for articlesWSJ_clean_final_<year>.db

### Table: `articles_index_cleaned`

| Column          | Type    | Description               |
|-----------------|---------|---------------------------|
| `id`            | INTEGER | Article index ID          |
| `year`          | TEXT    | Year of publication       |
| `month`         | TEXT    | Month of publication      |
| `day`           | TEXT    | Day of publication        |
| `headline`      | TEXT    | Article headline          |
| `article_time`  | TEXT    | Time of publication       |
| `keyword`       | TEXT    | Extracted keywords        |
| `link`          | TEXT    | Article URL               |
| `scraped_at`    | TEXT    | Scraping timestamp        |
| `scanned_status`| INTEGER | 0 = Not Scanned, 1 = Scanned |
| `section`       | TEXT    | Article section (e.g., Finance, Tech) |

---


### Table: `articles_index` (Final Version)

| Column          | Type    | Description               |
|-----------------|---------|---------------------------|
| `id`            | INTEGER | Article index ID          |
| `year`          | TEXT    | Year of publication       |
| `month`         | TEXT    | Month of publication      |
| `day`           | TEXT    | Day of publication        |
| `headline`      | TEXT    | Article headline          |
| `article_time`  | TEXT    | Time of publication       |
| `keyword`       | TEXT    | Extracted keywords        |
| `link`          | TEXT    | Article URL               |
| `scraped_at`    | TEXT    | Scraping timestamp        |
| `scanned_status`| INTEGER | 0 = Not Scanned, 1 = Scanned |
| `section`       | TEXT    | Article section (e.g., Finance, Tech) |

---

### Table: `article` (Final Version)

| Column        | Type      | Description                    |
|----------------|-----------|--------------------------------|
| `article_id`   | INTEGER   | Primary Key                   |
| `scanned_time` | TEXT      | Timestamp when scanned        |
| `title`        | TEXT      | Article title                 |
| `sub_title`    | TEXT      | Article subtitle              |
| `corpus`       | TEXT      | Full article text             |
| `index_id`     | INTEGER   | Foreign Key → `articles_index.id` |
| `section`      | TEXT      | Article section (e.g., Finance, Tech) |
| `date`         | TIMESTAMP | Consolidated publication date |

## 📖 Notes
- This README was created with the assistance of https://chatgpt.com/share/68262bcc-3174-8013-b3c0-932023530270
- Full scraping requires a **WSJ premium account** and manual Chrome start with remote debugging enabled:
  ```
  chrome.exe --remote-debugging-port=9222
  ```
- Databases are stored as SQLite `.db` files. 
- Initial versions follow this naming convention:
  `articlesWSJ_<year>.db`.
- Cleaned versions follow this naming convention:  
  `articlesWSJ_clean_final_<year>.db`.
- The project separates **metadata crawling** and **full content scraping** for improved efficiency and modularity.
- Legacy scripts remain for transparency and reproducibility but can be skipped if using the latest pipeline.
- The collected data will be used solely for the intended research purposes and will never be shared or used otherwise
- later analysis only utilizes articlesWSJ_clean_final_<year>.db for 2023 & 2024
