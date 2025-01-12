from src.crawler.utils.common_utils import fetch, get_daum_news_content, create_session, logger, seoul_tz, send_news_to_backend
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import traceback

# 키워드당 수집할 기사 수 : settings.py와 별개로 설정
ARTICLES_PER_KEYWORD = 5

def _build_search_url(search_str, sort, start_date, end_date, page):
    search_str = search_str.replace(" ", "%20")
    return f"https://search.daum.net/search?nil_suggest=btn&w=news&DA=PGD&cluster=y&q={search_str}&sort={sort}&sd={start_date}&ed={end_date}&period=u&p={page}"

def _extract_urls(soup):
    urls = []
    for title in soup.find_all('div', class_='item-title'):
        a_tag = title.find('a')
        if a_tag and 'href' in a_tag.attrs:
            urls.append(a_tag['href'])
    return urls

def get_url_list(session, search_str, last_crawl_time):
    url_list = []
    page = 1
    current_time = datetime.now(seoul_tz)
    twenty_four_hours_ago = current_time - timedelta(hours=24)
    
    start_date = (last_crawl_time if last_crawl_time and last_crawl_time > twenty_four_hours_ago 
                    else twenty_four_hours_ago).strftime("%Y%m%d%H%M%S")
    end_date = current_time.strftime("%Y%m%d%H%M%S")

    while len(url_list) < ARTICLES_PER_KEYWORD:
        url = _build_search_url(search_str, "recency", start_date, end_date, page)
        logger.info(f"크롤링 중인 페이지: {url}")
        
        soup = BeautifulSoup(fetch(session, url), 'html.parser')
        new_urls = _extract_urls(soup)
        
        logger.info(f"new_urls: {new_urls}")
        
        if not new_urls:
            break
            
        for new_url in new_urls:
            if new_url not in url_list:
                url_list.append(new_url)
                if len(url_list) >= ARTICLES_PER_KEYWORD:
                    return url_list[:ARTICLES_PER_KEYWORD]
            else:
                logger.info(f"중복 기사 발견. '{search_str}' 키워드 크롤링을 중단합니다.")
                return url_list
            
        page += 1
    
    return url_list

def is_ai_related_content(content: str) -> bool:
    # "AI학습 이용 금지" 문구 제거
    cleaned_content = content.replace("AI학습 이용 금지", "")
    cleaned_content = cleaned_content.replace("AI 데이터 활용 금지", "")
    
    # AI 관련 키워드 리스트
    ai_keywords = ["AI"]
    
    # 하나라도 AI 관련 키워드가 포함되어 있으면 True 반환
    return any(keyword in cleaned_content for keyword in ai_keywords)

def process_article(session, url, keyword, unique_articles):
    if url not in unique_articles:
        article = get_daum_news_content(session, url)
        if article and is_ai_related_content(article['content']):
            article['keywords'] = [keyword]
            article['tags'] = ['금융AI']
            unique_articles[url] = article
            logger.info(f"AI 관련 기사 발견: {article['title']}")
        else:
            logger.info(f"AI 관련 내용이 없는 기사 제외: {url}")
    elif keyword not in unique_articles[url]['keywords']:
        unique_articles[url]['keywords'].append(keyword)
        logger.info(f"중복된 URL에 키워드 추가: {url}, 키워드: {keyword}")

def crawl_finance_ai_news():
    start_time = datetime.now(seoul_tz)
    logger.info(f"금융 AI 뉴스 크롤링 작업 시작... (시작 시간: {start_time.isoformat()})")
    
    search_keywords = [
        "신한카드AI",
        "롯데카드AI",
        "비씨카드AI",
        "현대카드AI",
        "우리카드AI",
        "국민카드AI",
        "농협카드AI",
        "하나카드AI",
        "토스AI",
        "기업은행AI",
        "국민은행AI",
        "하나은행AI",
        "우리은행AI",
        "신한은행AI",
        "iM뱅크AI",
        "제일은행AI",
        "씨티은행AI",
        "케이뱅크AI",
        "카카오뱅크AI",
        "농협AI",
        "수협AI",
    ]
    
    try:
        session = create_session()
        unique_articles = {}
        twenty_four_hours_ago = start_time - timedelta(hours=24)

        for keyword in search_keywords:
            logger.info(f"'{keyword}' 키워드에 대한 뉴스 크롤링 시작")
            url_list = get_url_list(session, keyword, twenty_four_hours_ago)
            
            for url in url_list:
                process_article(session, url, keyword, unique_articles)
            
            logger.info(f"'{keyword}' 키워드에 대해 {len(url_list)}개의 기사를 크롤링했습니다.")

        news_list = list(unique_articles.values())
        if news_list:
            result = send_news_to_backend(news_list)
            logger.info(f"뉴스 전송 결과: {result}")
        else:
            logger.info("크롤링된 금융 AI 뉴스가 없습니다.")
            
        return news_list

    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        return []

if __name__ == "__main__":
    crawl_finance_ai_news()
