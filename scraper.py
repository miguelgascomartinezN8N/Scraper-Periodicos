import json
import os
import time
from datetime import datetime
from feed_reader import FeedReader
from article_scraper import ArticleScraper
from storage import Storage

class NewsScraper:
    def __init__(self, config_path='/home/ubuntu/news-scraper/config/feeds.json'):
        self.config_path = config_path
        self.config = self._load_config()
        self.storage = Storage()
        
        settings = self.config.get('settings', {})
        self.feed_reader = FeedReader(user_agent=settings.get('user_agent'))
        self.article_scraper = ArticleScraper(
            user_agent=settings.get('user_agent'),
            timeout=settings.get('request_timeout_seconds', 10),
            download_images=settings.get('download_images', True)
        )
        self.delay = settings.get('request_delay_seconds', 1)
        self.max_articles = settings.get('max_articles_per_feed', 10)

    def _load_config(self):
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def run(self):
        start_time = datetime.now().isoformat()
        feeds = [f for f in self.config.get('feeds', []) if f.get('enabled', True)]
        
        stats = {
            'start_time': start_time,
            'articles_found': 0,
            'articles_new': 0,
            'articles_skipped_duplicate': 0,
            'articles_skipped_domain': 0
        }
        
        all_new_articles = []
        
        for feed_config in feeds:
            print(f"Processing feed: {feed_config['name']})")
            try:
                entries = self.feed_reader.parse_feed(feed_config['url'])
            except Exception as e:
                print(f"Error parsing feed {feed_config['name']}: {e}")
                continue

            entries_to_process = entries[:self.max_articles]
            stats['articles_found'] += len(entries_to_process)
            
            for entry in entries_to_process:
                url = entry.get('link')
                if not url:
                    continue

                if self.storage.url_exists(url):
                    stats['articles_skipped_duplicate'] += 1
                    continue
                
                if self.storage.domain_exists(url):
                    stats['articles_skipped_domain'] += 1
                    continue
                
                print(f"Scraping article: {url}")
                article_data = self.article_scraper.scrape_article(url)
                
                if not article_data.get('success'):
                    print(f"Failed to scrape article: {url}")
                    continue

                full_article_data = {
                    **entry, 
                    **article_data
                }

                if not full_article_data.get('image_url') and entry.get('image_from_feed'):
                    full_article_data['image_url'] = entry['image_from_feed']
                
                article_id = self.storage.add_article(full_article_data)
                if article_id:
                    all_new_articles.append(full_article_data)
                    stats['articles_new'] += 1
                
                time.sleep(self.delay)
                
        stats['end_time'] = datetime.now().isoformat()
        self.storage.log_scrape_run(stats)
        
        if all_new_articles:
            date_str = datetime.now().strftime('%Y-%m-%d')
            self.storage.export_to_json(all_new_articles, date_str)
            
        return stats

if __name__ == "__main__":
    scraper = NewsScraper()
    result = scraper.run()
    print(f"Scraping completed. Results: {json.dumps(result, indent=2)}")
