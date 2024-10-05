import schedule
from time import sleep
import argparse
from src.crawler.news_crawler import crawl_daum_news

def job():
    print("뉴스 크롤링 작업 시작...")
    crawl_daum_news()
    print("뉴스 크롤링 작업 완료.")

def run_scheduler(time):
    schedule.every().day.at(time).do(job)
    print(f"뉴스 크롤러가 실행되었습니다. 매일 {time}에 크롤링을 수행합니다.")
    while True:
        schedule.run_pending()
        sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="다음 뉴스 크롤러")
    parser.add_argument("--immediate", action="store_true", help="즉시 실행 모드")
    args = parser.parse_args()

    time = "02:03"  # 기본 실행 시간

    if args.immediate:
        print("즉시 실행 모드로 크롤링을 시작합니다.")
        job()
    else:
        run_scheduler(time)