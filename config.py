import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")

if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_bot_token_here":
    raise ValueError("TELEGRAM_BOT_TOKEN이 .env 파일에 올바르게 설정되지 않았습니다.")
    
if not ADMIN_USER_ID or ADMIN_USER_ID == "123456789":
    raise ValueError("ADMIN_USER_ID가 .env 파일에 올바르게 설정되지 않았습니다.")

# ADMIN_USER_ID는 int 형태가 안전하므로 변환
try:
    ADMIN_USER_ID = int(ADMIN_USER_ID)
except ValueError:
    raise ValueError("ADMIN_USER_ID는 숫자 형식이어야 합니다.")
