from src.crawler.utils.common_utils import fetch, get_daum_news_content, create_session, logger
from bs4 import BeautifulSoup
import json
from src.config.settings import BACKEND_URL
import requests
import traceback

category_url = [
    {'category': '사회', 'url': 'https://news.daum.net/society#1'},
    {'category': '정치', 'url': 'https://news.daum.net/politics#1'},
    {'category': '경제', 'url': 'https://news.daum.net/economic#1'},
    {'category': '국제', 'url': 'https://news.daum.net/foreign#1'},
    {'category': '문화', 'url': 'https://news.daum.net/culture#1'},
    {'category': 'IT', 'url': 'https://news.daum.net/digital#1'}
]

def get_category_news(session, category_info):
    """카테고리별 뉴스 크롤링"""
    print("BACKEND_URL: ", BACKEND_URL)
    url = category_info['url']
    category = category_info['category']
    news_list = []
    
    try:
        html = fetch(session, url)
        soup = BeautifulSoup(html, 'html.parser')
        
        #for ul_class in ['list_mainnews', 'list_newsmajor']:
        for ul_class in ['list_newsheadline2']:
            news_section = soup.find('ul', class_=ul_class)
            print(news_section)
            if news_section:
                for item in news_section.find_all('li'):
                    try:
                        #link = item.find('a', class_='link_txt')['href']
                        link = item.find('a', class_='item_newsheadline2')['href']
                        article = get_daum_news_content(session, link)
                        if article:
                            article["tags"] = [category]
                            article["keywords"] = []
                            news_list.append(article)
                    except Exception as e:
                        logger.error(f"개별 기사 크롤링 중 오류 발생: {str(e)}")
                        continue
                        
        logger.info(f"{category} 카테고리 {len(news_list)}개 기사 크롤링 완료")
        return news_list
    
    except Exception as e:
        logger.error(f"{category} 카테고리 크롤링 중 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        return news_list

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

def crawl_daum_main_news():
    """메인 크롤링 함수"""
    try:
        session = create_session()
        logger.info("다음 뉴스 크롤링 시작")
        
        total_articles = 0
        for category_info in category_url:
            category = category_info['category']
            logger.info(f"{category} 카테고리 크롤링 시작")
            
            news_list = get_category_news(session, category_info)
            if news_list:
                result = send_news_to_backend(news_list)
                total_articles += len(news_list)
                logger.info(f"{category} 카테고리 {len(news_list)}개 기사 전송 완료")
                logger.info(f"전송 결과: {result}")
            else:
                logger.info(f"{category} 카테고리 크롤링된 뉴스가 없습니다.")
        
        logger.info(f"전체 크롤링 완료. 총 {total_articles}개 기사 처리")
        
    except Exception as e:
        logger.error(f"크롤링 프로세스 중 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    crawl_daum_main_news()
