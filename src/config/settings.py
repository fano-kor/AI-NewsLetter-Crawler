import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
ARTICLES_PER_KEYWORD = 10  # 키워드당 수집할 기사 수
ARTICLES_KEYWORDS= ["신용카드", "은행", "비씨카드", "BC카드"]
SLEEP_MIN = 1
SLEEP_MAX = 3

# Next URL 추가
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3000")  # 기본값 설정