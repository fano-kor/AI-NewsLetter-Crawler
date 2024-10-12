import random
from time import sleep
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pytz import timezone
import logging
#from sqlalchemy.orm import Session
#from src.database.db import SessionLocal
#from src.models.news import News
from src.config.settings import HEADERS, SLEEP_MIN, SLEEP_MAX, ARTICLES_PER_KEYWORD, ARTICLES_KEYWORDS, BACKEND_URL
import json
import os
from datetime import datetime

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
sort = "accuracy" # accuracy, recency, old

def fetch(session, url):
    sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))
    response = session.get(url)
    return response.text

def get_url_list(session, search_str):
    url_list = []
    page = 1
    while len(url_list) < ARTICLES_PER_KEYWORD:
        base_url = f"https://search.daum.net/search?nil_suggest=btn&w=news&DA=PGD&cluster=y&q={search_str}&sort={sort}&sd={start_date}&ed={end_date}&period=u&p={page}"
        logger.info(f"크롤링 중인 페이지: {base_url}")
        
        html = fetch(session, base_url)
        soup = BeautifulSoup(html, 'html.parser')
        
        titles = soup.find_all('div', class_='item-title')
        if not titles:
            break
        
        for title in titles:
            a_tag = title.find('a')
            if a_tag and 'href' in a_tag.attrs:
                link = a_tag['href']
                logger.info(f"URL : '{link}'")
                if link not in url_list:
                    url_list.append(link)
                    if len(url_list) >= ARTICLES_PER_KEYWORD:
                        return url_list
                else:
                    logger.info(f"중복 기사 발견. '{search_str}' 키워드 크롤링을 중단합니다.")
                    return url_list
        
        page += 1
    return url_list

def get_content(session, url, keyword):
    logger.info(f"Fetching content from: {url}")
    html = fetch(session, url)
    soup = BeautifulSoup(html, 'html.parser')
    
    title = soup.find('h3', class_='tit_view').get_text().strip()
    published_at = soup.find('span', class_='num_date').get_text().strip()
    content = soup.find('div', class_='article_view').get_text().replace('\n', ' ').strip()
    
    return {
        "title": title,
        "content": content,
        "published_at": published_at,
        "url": url,
        "keywords": [keyword]  # 키워드를 리스트로 변경
    }

def save_to_file(articles):
    if not articles:
        logger.info("저장할 기사가 없습니다.")
        return

    current_time = datetime.now(seoul_tz)
    filename = f"/result/{current_time.strftime('%Y%m%d')}.jsonl"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        for article in articles:
            json.dump(article, f, ensure_ascii=False)
            f.write('\n')
    logger.info(f"{len(articles)}개의 기사를 파일에 저장했습니다: {filename}")
    return filename

def send_file_to_backend(filename):
    url = f"{BACKEND_URL}/api/news"
    with open(filename, 'rb') as file:
        files = {'news.jsonl': file}
        try:
            response = requests.post(url, files=files)
            response.raise_for_status()  # 오류 발생 시 예외 발생
            logger.info(f"파일 전송 성공: {response.json()}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"파일 전송 중 오류 발생: {e}")
            return {"error": str(e)}

def crawl_daum_news():
    session = requests.Session()
    session.headers.update(HEADERS)
    
    unique_articles = {}  # URL을 키로 사용하여 기사를 저장

    for keyword in ARTICLES_KEYWORDS:
        logger.info(f"'{keyword}' 키워드에 대한 뉴스 크롤링 시작")
        url_list = get_url_list(session, keyword)
        
        for url in url_list:
            if url not in unique_articles:
                article = get_content(session, url, keyword)
                if article:
                    article['keywords'] = [keyword]  # 키워드 리스트로 변경
                    unique_articles[url] = article
            else:
                # 이미 존재하는 기사라면 키워드만 추가
                if keyword not in unique_articles[url]['keywords']:
                    unique_articles[url]['keywords'].append(keyword)
                logger.info(f"중복된 URL에 키워드 추가: {url}, 키워드: {keyword}")
        
        logger.info(f"'{keyword}' 키워드에 대해 {len(url_list)}개의 기사를 크롤링했습니다.")

    # 딕셔너리 값만 리스트로 변환하여 저장
    all_articles = list(unique_articles.values())
    filename = save_to_file(all_articles)
    
    # 파일 전송
    result = send_file_to_backend(filename)
    logger.info(f"파일 전송 결과: {result}")
