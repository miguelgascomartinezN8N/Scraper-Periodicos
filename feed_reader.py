import feedparser
from datetime import datetime
from dateutil import parser as date_parser

class FeedReader:
    def __init__(self, user_agent=None):
        self.user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

    def parse_feed(self, url):
        # Use feedparser to read the feed
        feed = feedparser.parse(url, agent=self.user_agent)
        entries = []
        
        for entry in feed.get('entries', []):
            normalized_entry = {
                'link': entry.get('link'),
                'title': entry.get('title'),
                'summary': entry.get('summary', ''),
                'published_date': self._normalize_date(entry),
                'author': entry.get('author', ''),
                'tags': [tag.get('term') for tag in entry.get('tags', []) if tag.get('term')] if 'tags' in entry else [],
                'image_from_feed': self._extract_image(entry)
            }
            if normalized_entry['link']:
                entries.append(normalized_entry)
                
        return entries

    def _normalize_date(self, entry):
        # Handle various date fields in feeds
        date_str = entry.get('published') or entry.get('updated') or entry.get('created') or entry.get('pubDate')
        if not date_str:
            return datetime.now().isoformat()
        
        try:
            # Use dateutil.parser for robust date parsing
            dt = date_parser.parse(date_str)
            # Ensure it's in ISO 8601 format
            return dt.isoformat()
        except Exception:
            # Fallback to current time if parsing fails
            return datetime.now().isoformat()

    def _extract_image(self, entry):
        # 1. media:content (Common in many feeds)
        if 'media_content' in entry:
            for content in entry.media_content:
                if 'url' in content and ('image' in content.get('type', '') or content.get('medium') == 'image'):
                    return content['url']
        
        # 2. Enclosures (Standard RSS 2.0)
        if 'enclosures' in entry:
            for enclosure in entry.enclosures:
                if 'url' in enclosure and ('image' in enclosure.get('type', '') or 'image' in enclosure.get('url', '')):
                    return enclosure['url']
                    
        # 3. media:thumbnail
        if 'media_thumbnail' in entry and len(entry.media_thumbnail) > 0:
            return entry.media_thumbnail[0].get('url')
        
        # 4. Atom feed specific images
        if 'links' in entry:
            for link in entry.links:
                if 'image' in link.get('type', ''):
                    return link.get('href')
                    
        return None
