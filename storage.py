import sqlite3
import json
import os
import hashlib
from datetime import datetime
from urllib.parse import urlparse

class Storage:
    def __init__(self, db_path=None):
        # Use relative path if none provided, ensuring it works in any environment
        if db_path is None:
            # Try to get from environment variable or use default relative path
            db_path = os.environ.get('DATABASE_PATH', 'data/news_scraper.db')
        
        # If the path is relative, make it absolute based on current working directory
        # but avoid hardcoding /home/ubuntu
        if not os.path.isabs(db_path):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(base_dir, db_path)
        else:
            self.db_path = db_path
            
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Table for articles
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE,
                    domain TEXT,
                    title TEXT,
                    text TEXT,
                    summary TEXT,
                    image_url TEXT,
                    local_image_path TEXT,
                    author TEXT,
                    published_date TEXT,
                    tags TEXT,
                    used BOOLEAN DEFAULT FALSE,
                    success BOOLEAN,
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Table for processed URLs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_urls (
                    url TEXT PRIMARY KEY,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Table for scrape runs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scrape_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    articles_found INTEGER,
                    articles_new INTEGER,
                    articles_skipped_duplicate INTEGER,
                    articles_skipped_domain INTEGER
                )
            ''')
            conn.commit()

    def url_exists(self, url):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM processed_urls WHERE url = ?', (url,))
            return cursor.fetchone() is not None

    def domain_exists(self, url):
        domain = urlparse(url).netloc
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM articles WHERE domain = ?', (domain,))
            return cursor.fetchone() is not None

    def add_article(self, article_data):
        domain = urlparse(article_data['url']).netloc
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                # Handle tags which might be a list
                tags_json = json.dumps(article_data.get('tags', [])) if isinstance(article_data.get('tags'), list) else article_data.get('tags', '[]')
                
                cursor.execute('''
                    INSERT INTO articles (
                        url, domain, title, text, summary, image_url, 
                        local_image_path, author, published_date, tags, success
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article_data['url'], domain, article_data['title'], 
                    article_data.get('text'), article_data.get('summary'), 
                    article_data.get('image_url'), article_data.get('local_image_path'),
                    article_data.get('author'), article_data.get('published_date'),
                    tags_json, article_data.get('success', True)
                ))
                cursor.execute('INSERT OR IGNORE INTO processed_urls (url) VALUES (?)', (article_data['url'],))
                conn.commit()
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                return None

    def mark_as_used(self, article_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE articles SET used = TRUE WHERE id = ?', (article_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_news_list(self, page=1, page_size=10):
        offset = (page - 1) * page_size
        today = datetime.now().strftime('%Y-%m-%d')
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Filter by today's date and used=False
            cursor.execute('''
                SELECT id, title, summary, url, published_date FROM articles 
                WHERE used = FALSE AND published_date LIKE ?
                ORDER BY published_date DESC
                LIMIT ? OFFSET ?
            ''', (f'{today}%', page_size, offset))
            return [dict(row) for row in cursor.fetchall()]

    def get_article_by_id(self, article_id):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM articles WHERE id = ?', (article_id,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                try:
                    data['tags'] = json.loads(data['tags'])
                except:
                    data['tags'] = []
                return data
            return None

    def log_scrape_run(self, run_data):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scrape_runs (
                    start_time, end_time, articles_found, 
                    articles_new, articles_skipped_duplicate, articles_skipped_domain
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                run_data['start_time'], run_data['end_time'], 
                run_data['articles_found'], run_data['articles_new'],
                run_data['articles_skipped_duplicate'], run_data['articles_skipped_domain']
            ))
            conn.commit()

    def clear_database(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM articles')
            cursor.execute('DELETE FROM processed_urls')
            cursor.execute('DELETE FROM scrape_runs')
            conn.commit()
            return True

    def export_to_json(self, articles, date_str):
        # Relative path for exports
        base_dir = os.path.join(os.path.dirname(self.db_path), '..', 'output', date_str)
        articles_dir = os.path.join(base_dir, 'articles')
        os.makedirs(articles_dir, exist_ok=True)
        
        # Save individual articles
        for article in articles:
            url_hash = hashlib.md5(article['url'].encode()).hexdigest()
            with open(os.path.join(articles_dir, f'{url_hash}.json'), 'w', encoding='utf-8') as f:
                json.dump(article, f, ensure_ascii=False, indent=2)
        
        # Save consolidated JSON
        with open(os.path.join(base_dir, f'articles_{date_str}.json'), 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
