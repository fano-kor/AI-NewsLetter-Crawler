from src.crawler.daum.daum_keyword_news import crawl_daum_keyword_news
from src.crawler.daum.daum_main_news import crawl_daum_main_news
from src.crawler.aitimes.aitimes_news import crawl_aitimes_news
from src.crawler.finance_ai.finance_ai_news import crawl_finance_ai_news
from src.crawler.boan_news.boan_news import crawl_boan_news
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

def job_aitimes_news():
    logger.info("AI Times 뉴스 크롤링 작업 시작...")
    crawl_aitimes_news()
    logger.info("AI Times 뉴스 크롤링 작업 완료.")

def job_financial_ai_news():
    logger.info("Financial AI 뉴스 크롤링 작업 시작...")
    crawl_finance_ai_news()
    logger.info("Financial AI 뉴스 크롤링 작업 완료.")

'''
AWS Lambda 실행을 위한 함수
'''
def lambda_handler(event, context):
    print("Crawling starts")
    job_keyword_news()
    job_main_news()
    job_aitimes_news()
    job_financial_ai_news()
    crawl_boan_news()
    return {
        'statusCode': 200,
        'body': json.dumps("upload success")
    }

if __name__ == "__main__":
    lambda_handler(None, None)
