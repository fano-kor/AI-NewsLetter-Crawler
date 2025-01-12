import requests
import logging
import traceback
import json

# 로깅 설정
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

BACKEND_URL = "http://localhost:3000"

def send_file_to_backend(filename):
    url = f"{BACKEND_URL}/api/public/news"
    with open(filename, 'rb') as file:
        files = {'news.jsonl': file}
        try:
            response = requests.post(url, files=files)
            response.raise_for_status()
            logger.info(f"파일 전송 성공: {response}")
            logger.info(f"파일 전송 성공: {response.json()}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"파일 전송 중 오류 발생: {str(e)}")
            logger.error(traceback.format_exc())
            return {"error": str(e)}
        except json.JSONDecodeError as e:
            logger.error(f"JSON 디코딩 중 오류 발생: {str(e)}")
            logger.error(f"응답 내용: {response.text}")
            logger.error(traceback.format_exc())
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"예상치 못한 오류 발생: {str(e)}")
            logger.error(traceback.format_exc())
            return {"error": str(e)}

# 사용 예
try:
    data = send_file_to_backend('/result/20241015.jsonl')
except Exception as e:
    logger.error(f"예상치 못한 오류 발생: {str(e)}\n{traceback.format_exc()}")
