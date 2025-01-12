import requests
import random
import time
import json
import traceback
import logging
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from src.config.settings import BACKEND_URL
from src.config.settings import HEADERS, SLEEP_MIN, SLEEP_MAX
from src.crawler.utils.common_utils import get_image_as_base64
from pytz import timezone
import certifi

# 상수 정의
SEOUL_TIMEZONE = 'Asia/Seoul'

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def send_news_to_backend(news_list):
    """뉴스 데이터 백엔드 전송"""
    url = f"{BACKEND_URL}/api/public/news"
    try:
        response = requests.post(url, json=news_list)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"데이터 전송 중 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}

def parse_published_date(date_str):
    """날짜 문자열을 파싱하여 timezone 적용된 datetime 객체 반환"""
    try:
        published_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        return timezone(SEOUL_TIMEZONE).localize(published_at)
    except ValueError:
        logger.error(f"날짜 파싱 오류: {date_str}")
        return None

def extract_article_content(article_soup):
    """기사 내용과 이미지 추출"""
    content_div = article_soup.select_one('#news_content')
    if not content_div:
        return None, None
    
    content = content_div.text.strip()
    image_data = None
    image_tag = content_div.find('img')
    if image_tag and 'src' in image_tag.attrs:
        image_url = image_tag['src']
        if not image_url.startswith('http'):
            image_url = f"https://boannews.com{image_url}"
        image_data = get_image_as_base64(image_url)
    
    return content, image_data

def process_article(article, headers, twenty_four_hours_ago):
    """개별 기사 처리"""
    try:
        # 날짜 정보 먼저 확인
        date_element = article.select_one('.news_writer')
        if not date_element:
            return None, False
            
        # "조재호 기자 | 2024년 11월 11일 20:28" 형식에서 날짜 추출
        date_str = date_element.text.split('|')[-1].strip()
        published_at = datetime.strptime(date_str, '%Y년 %m월 %d일 %H:%M')
        published_at = timezone(SEOUL_TIMEZONE).localize(published_at)
        
        # 24시간 이전 기사는 크롤링하지 않음
        if published_at < twenty_four_hours_ago:
            return None, True
            
        # 링크 추출
        link_element = article.select_one('a')
        if not link_element:
            return None, False
        link = link_element.get('href')
        if not link.startswith('http'):
            link = f"https://boannews.com{link}"
            
        # 제목 추출
        title_element = article.select_one('.news_txt')
        if not title_element:
            return None, False
        title = title_element.text.strip()
        
        # 기사 내용 가져오기
        article_response = requests.get(link, headers=headers, verify=False)
        article_soup = BeautifulSoup(article_response.text, 'html.parser')
        
        content, image_data = extract_article_content(article_soup)
        if not content:
            return None, False
        
        article = {
            "title": title,
            "content": content,
            "published_at": published_at.isoformat(),
            "url": link,
            "tags": ["보안"],
            "thumbnail_image": image_data
        }
        
        return article, False
        
    except Exception as e:
        logger.error(f"기사 처리 중 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        return None, False

def get_article_list(page):
    """특정 페이지의 기사 목록을 가져옴"""
    base_url = "https://boannews.com/media/t_list.asp"
    params = {
        'page': str(page)
    }
    try:
        response = requests.get(
            base_url, 
            params=params, 
            headers=HEADERS,
            verify=False
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        article_list = soup.select('.news_list')
        return article_list
    except Exception as e:
        logger.error(f"페이지 {page} 크롤링 중 오류 발생: {e}")
        return []

def process_page(page, headers, twenty_four_hours_ago):
    """단일 페이지의 기사들을 처리"""
    articles = []
    article_list = get_article_list(page)
    
    for article in article_list:
        try:
            article_data, stop_crawling = process_article(article, headers, twenty_four_hours_ago)
            if stop_crawling:
                return articles, True
            if article_data:
                articles.append(article_data)
        except Exception as e:
            logger.error(f"기사 처리 중 오류 발생: {e}", exc_info=True)
        finally:
            time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))
    
    return articles, False

def crawl_boan_news():
    """보안뉴스 크롤링 메인 함수"""
    articles = []
    now = timezone(SEOUL_TIMEZONE).localize(datetime.now())
    twenty_four_hours_ago = now - timedelta(hours=24)
    
    try:
        for page in range(1, 5):
            page_articles, should_stop = process_page(page, HEADERS, twenty_four_hours_ago)
            articles.extend(page_articles)
            if should_stop:
                break
        
        if articles:
            result = send_news_to_backend(articles)
            logger.info(f"전송 결과: {result}")
        
        logger.info(f"총 {len(articles)}개의 기사를 크롤링했습니다.")
        return None
        
    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    crawl_boan_news()
