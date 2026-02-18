import requests
import trafilatura
from bs4 import BeautifulSoup
import hashlib
import os
from urllib.parse import urljoin, urlparse

class ArticleScraper:
    def __init__(self, user_agent=None, timeout=10, download_images=True):
        self.user_agent = user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        self.timeout = timeout
        self.download_images = download_images
        self.headers = {'User-Agent': self.user_agent}
        
        # Base directory for the project to ensure relative paths work
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def scrape_article(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            html = response.text
            
            # 1. Title Extraction
            title = self._extract_title(html)
            
            # 2. Main Content Extraction
            content = trafilatura.extract(html, include_images=True)
            if not content:
                content = self._fallback_content_extraction(html)
                
            # 3. Main Image Extraction
            image_url = self._extract_main_image(html, url)
            local_image_path = None
            if self.download_images and image_url:
                local_image_path = self._download_image(image_url)
                
            return {
                'url': url,
                'title': title,
                'text': content,
                'image_url': image_url,
                'local_image_path': local_image_path,
                'success': True if content else False
            }
        except Exception as e:
            return {
                'url': url,
                'title': "Error",
                'text': None,
                'success': False,
                'error': str(e)
            }

    def _extract_title(self, html):
        soup = BeautifulSoup(html, 'lxml')
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title.get('content')
            
        tw_title = soup.find('meta', name='twitter:title')
        if tw_title and tw_title.get('content'):
            return tw_title.get('content')
            
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
            
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
            
        return "No Title Found"

    def _fallback_content_extraction(self, html):
        soup = BeautifulSoup(html, 'lxml')
        for selector in ['article', '.article-body', '.entry-content', '.post-content', 'main']:
            element = soup.select_one(selector)
            if element:
                return element.get_text(separator='\n').strip()
        
        content_div = soup.find('div', class_=lambda x: x and ('article' in x or 'content' in x or 'body' in x))
        if content_div:
            return content_div.get_text(separator='\n').strip()
            
        return None

    def _extract_main_image(self, html, base_url):
        soup = BeautifulSoup(html, 'lxml')
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return urljoin(base_url, og_image.get('content'))
            
        tw_image = soup.find('meta', name='twitter:image')
        if tw_image and tw_image.get('content'):
            return urljoin(base_url, tw_image.get('content'))
            
        article = soup.find('article') or soup.find('main')
        if article:
            img = article.find('img')
            if img and img.get('src'):
                return urljoin(base_url, img.get('src'))
                
        return None

    def _download_image(self, url):
        try:
            # Use path relative to the script's directory
            images_dir = os.path.join(self.base_dir, 'output', 'images')
            os.makedirs(images_dir, exist_ok=True)
            
            response = requests.get(url, headers=self.headers, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            url_hash = hashlib.md5(url.encode()).hexdigest()
            parsed_url = urlparse(url)
            ext = os.path.splitext(parsed_url.path)[1]
            if not ext or len(ext) > 5:
                ext = '.jpg'
                
            filename = f"{url_hash}{ext}"
            filepath = os.path.join(images_dir, filename)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filepath
        except Exception:
            return None
