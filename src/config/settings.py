import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
SEARCH_WORDS = ["AI", "인공지능", "머신러닝", "딥러닝"]
SLEEP_MIN = 1
SLEEP_MAX = 3