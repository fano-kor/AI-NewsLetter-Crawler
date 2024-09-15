import asyncio
from src.crawler.news_crawler import crawl_daum_news

if __name__ == "__main__":
    asyncio.run(crawl_daum_news())