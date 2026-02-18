from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from scraper import NewsScraper
from storage import Storage
import json

app = FastAPI(
    title="News Scraper API",
    description="API for scraping and managing news articles from RSS feeds",
    version="1.0.0"
)

storage = Storage()

# Pydantic Models for request/response validation
class ArticlePreview(BaseModel):
    id: int
    title: str
    summary: str
    url: str
    published_date: str

class ArticleDetail(BaseModel):
    id: int
    url: str
    domain: str
    title: str
    text: Optional[str] = None
    summary: str
    image_url: Optional[str] = None
    local_image_path: Optional[str] = None
    author: str
    published_date: str
    tags: List[str]
    used: bool
    success: bool
    scraped_at: str

class ScrapeResponse(BaseModel):
    start_time: str
    end_time: str
    articles_found: int
    articles_new: int
    articles_skipped_duplicate: int
    articles_skipped_domain: int

class NewsListResponse(BaseModel):
    items: List[ArticlePreview]
    page: int
    page_size: int

# Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker HEALTHCHECK."""
    return {"status": "healthy"}

@app.post("/scrape-feeds", response_model=ScrapeResponse)
async def scrape_feeds():
    """
    Initiates the scraping process for all configured feeds.
    
    This endpoint runs synchronously and returns a summary of the execution
    including the number of new articles, duplicates skipped, and domain duplicates.
    """
    try:
        scraper = NewsScraper()
        result = scraper.run()
        return ScrapeResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.get("/get-news-list", response_model=NewsListResponse)
async def get_news_list(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100)):
    """
    Returns a paginated list of news articles from today.
    
    Only returns articles that:
    - Are from today (based on published_date)
    - Have not been marked as used (used=False)
    """
    try:
        articles = storage.get_news_list(page=page, page_size=page_size)
        return NewsListResponse(items=articles, page=page, page_size=page_size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve news list: {str(e)}")

@app.get("/read-full-news/{article_id}", response_model=ArticleDetail)
async def read_full_news(article_id: int):
    """
    Returns the complete details of a specific article.
    
    Includes all extracted information: title, full text, images, author, tags, etc.
    """
    try:
        article = storage.get_article_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        return ArticleDetail(**article)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve article: {str(e)}")

@app.post("/mark-news-as-used/{article_id}")
async def mark_news_as_used(article_id: int):
    """
    Marks an article as used (used=True).
    
    After marking, the article will not appear in future /get-news-list requests.
    """
    try:
        success = storage.mark_as_used(article_id)
        if not success:
            raise HTTPException(status_code=404, detail="Article not found")
        return {"message": "Article marked as used", "article_id": article_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark article as used: {str(e)}")

@app.delete("/clear-database")
async def clear_database():
    """
    Clears all data from the database.
    
    This includes articles, processed URLs, and scrape runs.
    Use with caution as this operation is irreversible.
    """
    try:
        storage.clear_database()
        return {"message": "Database cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear database: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
