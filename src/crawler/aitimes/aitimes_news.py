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
    except json.JSONDecodeError as e:
        logger.error(f"JSON 디코딩 오류: {str(e)}")
        logger.error(f"응답 내용: {response.text}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        return {"error": str(e)}

def crawl_aitimes_news():
    url = "https://www.aitimes.com/news/articleList.html?view_type=sm"
    # 결과를 저장할 리스트
    articles = []
    
    try:
        # 현재 시각과 24시간 전 시각 계산
        now = timezone('Asia/Seoul').localize(datetime.now())
        twenty_four_hours_ago = now - timedelta(hours=24)

        # 페이지 요청
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # BeautifulSoup으로 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 기사 목록 찾기
        article_list = soup.find('section', id='section-list').find_all('li')
        
        for article in article_list:
            try:
                # 기사 제목
                title_tag = article.find('h4', class_='titles')
                if title_tag:
                    title = title_tag.text.strip()
                else:
                    continue

                # 발행일시
                published_at_str = article.find('span', class_='byline').find_all('em')[1].text.strip()

                try:
                    # 날짜 파싱 형식 수정
                    published_at = datetime.strptime(published_at_str, "%Y.%m.%d %H:%M")
                    published_at = timezone('Asia/Seoul').localize(published_at)
                except ValueError:
                    logger.error(f"날짜 파싱 오류: {published_at_str}")
                    published_at = None
                
                # 24시간 이내의 기사만 수집
                if published_at and published_at >= twenty_four_hours_ago:
                    # 기사 링크
                    link = title_tag.find('a')['href']
                    full_link = f"https://www.aitimes.com{link}"
                    
                    # 개별 기사 페이지 접근
                    article_response = requests.get(full_link, headers=headers)
                    article_soup = BeautifulSoup(article_response.text, 'html.parser')
                    
                    # 기사 내용
                    content_div = article_soup.find(id='article-view-content-div')
                    content = content_div.text.strip()

                    # 이미지 데이터 추출
                    image_data = None
                    image_tag = content_div.find('img')  # 이미지 태그 찾기
                    if image_tag and 'src' in image_tag.attrs:
                        image_url = image_tag['src']  # 첫 번째 이미지만 저장
                        image_data = get_image_as_base64(image_url)
                    #print(content)
                    # 결과 저장
                    articles.append({
                        "title": title,
                        "content": content,
                        "published_at": published_at.isoformat() if published_at else None,
                        "url": full_link,
                        "tags": ["AI"],
                        "thumbnail_image": image_data
                    })
                
            except Exception as e:
                logger.error(f"Error processing article: {e}", exc_info=True)

            finally:
                # 서버 부하 방지를 위한 딜레이
                time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))
        
        # DataFrame으로 변환
        #print(articles)
        
        # 백엔드로 뉴스 데이터 전송
        if articles:
            result = send_news_to_backend(articles)
            logger.info(f"전송 결과: {result}")
        
        logger.info(f"Successfully crawled {len(articles)} articles")
        return None
        
    except Exception as e:
        logger.error(f"Error crawling website: {e}")
        return None

# 크롤링 실행
if __name__ == "__main__":
    crawl_aitimes_news()