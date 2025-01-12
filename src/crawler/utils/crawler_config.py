import logging
from datetime import datetime
from pytz import timezone
import requests
from src.config.settings import BACKEND_URL

logger = logging.getLogger(__name__)
seoul_tz = timezone('Asia/Seoul')

class CrawlerConfig:
    def update_last_crawled_times(self, keywords, start_time):
        data = [{"keyword": keyword, "last_crawled_dt": start_time.isoformat()} for keyword in keywords]
        
        url = f"{BACKEND_URL}/api/public/keywords/last-crawled-dt"
        try:
            response = requests.put(url, json=data)
            response.raise_for_status()
            logger.info(f"최종 크롤링 시간 업데이트 성공: {response.json()}")
            
        except requests.RequestException as e:
            logger.error(f"최종 크롤링 시간 업데이트 실패: {str(e)}")
        except Exception as e:
            logger.error(f"예상치 못한 오류 발생: {str(e)}")

    def get_last_crawled_time(self, keyword):
        return self.config.get(keyword)

    def get_all_last_crawled_times(self):
        return self.config
