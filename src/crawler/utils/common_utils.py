import random
from time import sleep
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pytz import timezone
import logging
import base64
import traceback
import json
from src.config.settings import HEADERS, SLEEP_MIN, SLEEP_MAX, BACKEND_URL

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 시간 설정
seoul_tz = timezone('Asia/Seoul')

def fetch(session, url):
    sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))
    response = session.get(url)
    return response.text

def get_image_as_base64(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        return base64.b64encode(response.content).decode('utf-8')
    except requests.RequestException as e:
        logger.error(f"이미지 다운로드 중 오류 발생: {e}")
        return None
    
def send_file_to_backend(filename):
    url = f"{BACKEND_URL}/api/public/news"
    with open(filename, 'rb') as file:
        files = {'news.jsonl': file}
        try:
            response = requests.post(url, files=files)
            response.raise_for_status()
            logger.info(f"파일 전송 성공: {response.json()}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"파일 전송 중 오류 발생: {e}")
            return {"error": str(e)}
    
def send_news_to_backend(news_list):
    url = f"{BACKEND_URL}/api/public/news"
    try:
        response = requests.post(url, json=news_list)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"파일 전송 중 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}
    except json.JSONDecodeError as e:
        logger.error(f"JSON 디코딩 오류: {e}")
        logger.error(f"응답 내용: {response.text}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}    

def get_daum_news_content(session, url):
    logger.info(f"Fetching content from: {url}")
    html = fetch(session, url)
    soup = BeautifulSoup(html, 'html.parser')
    
    title = soup.find('h3', class_='tit_view').get_text().strip()
    published_at_str = soup.find('span', class_='num_date').get_text().strip()
    
    # content 처리 부분 수정
    content_div = soup.find('div', class_='article_view')
    content_parts = []
    
    # 본문 내용 수집
    for element in content_div.find_all(['p', 'div'], {'dmcf-ptype': 'general'}):
        text = element.get_text().strip()
        if text and not text.startswith('Copyright'):  # 저작권 문구 제외
            content_parts.append(text)
    
    # 이미지 캡션 수집
    for caption in content_div.find_all('figcaption', class_='txt_caption'):
        text = caption.get_text().strip()
        if text:
            content_parts.append(f"[사진] {text}")
    
    # 개행문자로 구분하여 하나의 문자열로 결합
    content = '\n\n'.join(content_parts)
    
    try:
        published_at = datetime.strptime(published_at_str, "%Y. %m. %d. %H:%M")
        published_at = seoul_tz.localize(published_at)
    except ValueError:
        logger.error(f"날짜 파싱 오류: {published_at_str}")
        published_at = None
    
    image_data = None
    if content_div:
        thumb_image = content_div.find('img', class_='thumb_g_article')
        if thumb_image and 'src' in thumb_image.attrs:
            image_url = thumb_image['src']
            image_data = get_image_as_base64(image_url)
    
    return {
        "title": title,
        "content": content,
        "published_at": published_at.isoformat() if published_at else None,
        "url": url,
        #"keywords": [keyword],
        "thumbnail_image": image_data
    }

def create_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    return session
