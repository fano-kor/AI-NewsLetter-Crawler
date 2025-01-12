import schedule
from time import sleep
import argparse
from src.crawler.daum.daum_keyword_news import crawl_daum_keyword_news
from src.crawler.daum.daum_main_news import crawl_daum_main_news
from src.crawler.aitimes.aitimes_news import crawl_aitimes_articles
import logging
import json

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def job_keyword_news():
    logger.info("다음 키워드 뉴스 크롤링 작업 시작...")
    crawl_daum_keyword_news()
    logger.info("다음 키워드 뉴스 크롤링 작업 완료.")

def job_main_news():
    logger.info("다음 IT 뉴스 크롤링 작업 시작...")
    crawl_daum_main_news()
    logger.info("다음 IT 뉴스 크롤링 작업 완료.")

def run_scheduler():
    # 키워드 뉴스 크롤링 (매시 정각마다)
    schedule.every().hour.at(":00").do(job_keyword_news)
    
    # IT 뉴스 크롤링 (0, 3, 6, 9, 12, 15, 18, 21시마다)
    for hour in [0, 3, 6, 9, 12, 15, 18, 21]:
        schedule.every().day.at(f"{hour:02d}:10").do(job_main_news)
    
    logger.info("뉴스 크롤러가 실행되었습니다.")
    logger.info("키워드 뉴스: 매시 정각마다 크롤링")
    logger.info("IT 뉴스: 0, 3, 6, 9, 12, 15, 18, 21시마다 크롤링")
    
    while True:
        schedule.run_pending()
        sleep(1)

'''
AWS Lambda 실행을 위한 함수
'''
def lambda_handler(event, context):
    print("Crawling starts")
    job_keyword_news()
    job_main_news()
    return {
        'statusCode': 200,
        'body': json.dumps("upload success")
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="다음 뉴스 크롤러")
    parser.add_argument("--immediate", "-i", action="store_true", help="즉시 실행 모드")
    args = parser.parse_args()

    if args.immediate:
        logger.info("즉시 실행 모드로 크롤링을 시작합니다.")
        job_keyword_news()
        job_main_news()
    else:
        run_scheduler()

