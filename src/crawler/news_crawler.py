import asyncio
import random
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pytz import timezone
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from src.database.db import async_engine
from src.models.news import News
from src.config.settings import HEADERS, SEARCH_WORDS, SLEEP_MIN, SLEEP_MAX

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 시간 설정
seoul_tz = timezone('Asia/Seoul')
current_time = datetime.now(seoul_tz)
yesterday = current_time - timedelta(days=1)
date_str = yesterday.strftime("%Y%m%d")
start_date = f"{date_str}000000"
end_date = f"{date_str}235959"

async def fetch(session, url):
    await asyncio.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))
    async with session.get(url) as response:
        return await response.text()

async def get_url_list(session, search_str):
    url_list = []
    page = 1
    while True:
        base_url = f"https://search.daum.net/search?nil_suggest=btn&w=news&DA=PGD&cluster=y&q={search_str}&sort=old&sd={start_date}&ed={end_date}&period=u&p={page}"
        logger.info(f"Crawling page: {base_url}")
        
        html = await fetch(session, base_url)
        soup = BeautifulSoup(html, 'html.parser')
        
        titles = soup.find_all('div', class_='item-title')
        if not titles:
            break
        
        for title in titles:
            a_tag = title.find('a')
            if a_tag and 'href' in a_tag.attrs:
                link = a_tag['href']
                if link not in url_list:
                    url_list.append(link)
                else:
                    return url_list
        page += 1
    return url_list
async def get_content(session, url):
    logger.info(f"Fetching content from: {url}")
    html = await fetch(session, url)
    soup = BeautifulSoup(html, 'html.parser')
    
    title = soup.find('h3', class_='tit_view').get_text().strip()
    write_date = soup.find('span', class_='num_date').get_text().strip()
    content = soup.find('div', class_='article_view').get_text().replace('\n', ' ').strip()
    
    return {
        "title": title,
        "content": content,
        "write_date": write_date,
        "url": url
    }

async def save_to_database(db: AsyncSession, articles):
    for article in articles:
        news = News(
            title=article['title'],
            content=article['content'],
            url=article['url'],
            published_at=datetime.strptime(article['write_date'], "%Y.%m.%d. %H:%M"),
            source="Daum",
            crawled_at=datetime.now(seoul_tz)
        )
        db.add(news)
    await db.commit()
    logger.info(f"Saved {len(articles)} articles to the database")

async def crawl_daum_news():
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        url_lists = await asyncio.gather(*[get_url_list(session, word) for word in SEARCH_WORDS])
        all_urls = list(set([url for sublist in url_lists for url in sublist]))
        
        articles = await asyncio.gather(*[get_content(session, url) for url in all_urls])
        
        async_session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as db:
            await save_to_database(db, articles)
def crawl_news_wrapper():
    asyncio.run(crawl_daum_news())