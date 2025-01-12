from src.crawler.utils.common_utils import fetch, get_daum_news_content, create_session, logger, seoul_tz, send_news_to_backend
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import os
from src.config.settings import ARTICLES_PER_KEYWORD, BACKEND_URL
import requests
from src.crawler.utils.crawler_config import CrawlerConfig
import traceback

def get_url_list(session, search_str, last_crawl_time):
    url_list = []
    page = 1
    current_time = datetime.now(seoul_tz)
    
    # 24시간 전 시각 계산
    twenty_four_hours_ago = current_time - timedelta(hours=24)

    if last_crawl_time and last_crawl_time > twenty_four_hours_ago:
        start_date = last_crawl_time.strftime("%Y%m%d%H%M%S")
    else:
        start_date = twenty_four_hours_ago.strftime("%Y%m%d%H%M%S")
    
    end_date = current_time.strftime("%Y%m%d%H%M%S")
    #sort = "recency"
    sort = "accuracy"

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

def get_keywords_from_api():
    url = f"{BACKEND_URL}/api/public/keywords"
    try:
        response = requests.get(url)
        response.raise_for_status()
        keywords_json = response.json()
        logger.info(f"API에서 가져온 키워드: {keywords_json}")
        return keywords_json
    except requests.RequestException as e:
        logger.error(f"키워드 가져오기 실패: {e}")
        logger.error(traceback.format_exc())
        return []
    except json.JSONDecodeError as e:
        logger.error(f"JSON 디코딩 오류: {e}")
        logger.error(f"응답 내용: {response.text}")
        logger.error(traceback.format_exc())
        return []

def crawl_daum_keyword_news():
    start_time = datetime.now(seoul_tz)
    logger.info(f"다음 키워드 뉴스 크롤링 작업 시작... (시작 시간: {start_time.isoformat()})")
    
    try:
        session = create_session()
        unique_articles = {}
        crawler_config = CrawlerConfig()
        twenty_four_hours_ago = start_time - timedelta(hours=24)

        keywords_jsonArr = get_keywords_from_api()
        if not keywords_jsonArr:
            logger.error("키워드를 가져오지 못했습니다. 크롤링을 중단합니다.")
            return []

        crawled_keywords = []
        for json in keywords_jsonArr:
            keyword = json['keyword']
            last_crawled_at = json['lastCrawledAt']
            logger.info(f"'{keyword}' 키워드에 대한 뉴스 크롤링 시작")
            
            if last_crawled_at:
                last_crawl_time = datetime.fromisoformat(last_crawled_at)
                if last_crawl_time.tzinfo is None:
                    last_crawl_time = seoul_tz.localize(last_crawl_time)
                if last_crawl_time < twenty_four_hours_ago:
                    last_crawl_time = twenty_four_hours_ago
            else:
                last_crawl_time = twenty_four_hours_ago
            
            url_list = get_url_list(session, keyword, last_crawl_time)
            
            for url in url_list:
                if url not in unique_articles:
                    article = get_daum_news_content(session, url)
                    if article:
                        article['keywords'] = [keyword]
                        article['tags'] = [keyword] #일단 키워드와 태그를 동일하게 하자 "KT, BCCARD"
                        unique_articles[url] = article
                elif keyword not in unique_articles[url]['keywords']:
                    unique_articles[url]['keywords'].append(keyword)
                    logger.info(f"중복된 URL에 키워드 추가: {url}, 키워드: {keyword}")
            
            logger.info(f"'{keyword}' 키워드에 대해 {len(url_list)}개의 기사를 크롤링했습니다.")
            crawled_keywords.append(keyword)
            
            # 크롤링이 완료된 후 마지막 크롤링 시간 업데이트
            crawler_config.update_last_crawled_times(crawled_keywords, start_time)

        news_list = list(unique_articles.values())
        if news_list:
            #filename = save_to_file(news_list)
            #result = send_file_to_backend(filename)
            result = send_news_to_backend(news_list)
            logger.info(f"파일 전송 결과: {result}")
        else:
            logger.info("크롤링된 IT 뉴스가 없습니다.")
        logger.info(f"파일 전송 결과: {result}")
    except Exception as e:
        logger.error(f"크롤링 중 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        return []
