import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

from config import TELEGRAM_BOT_TOKEN, ADMIN_USER_ID
from utils import parse_investing_search

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def get_stock_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/get 명령어 핸들러: 종목을 검색하고 결과를 회신합니다."""
    user_id = update.effective_user.id
    
    # 명령어 파라미터 가져오기 (예: '/get AAPL' -> 'AAPL')
    if not context.args:
        await update.message.reply_text("검색할 종목명이나 코드를 입력해주세요. \n예시: `/get AAPL` 또는 `/get 삼성전자`", parse_mode='Markdown')
        return
        
    query = " ".join(context.args)
    logger.info(f"사용자({user_id}) 종목 검색 요청: {query}")

    # 권한 검사 (선택 사항: 원치 않으시면 이 부분을 주석 처리하면 누구나 쓸 수 있습니다)
    if user_id != ADMIN_USER_ID:
        logger.warning(f"권한 없는 사용자({user_id}) 접근 시도 차단.")
        await update.message.reply_text(f"⛔️ 접근 권한이 없습니다. (ID: {user_id})")
        return

    # 안내 메시지
    status_msg = await update.message.reply_text(f"⏳ **'{query}'** 종목을 검색 중입니다...", parse_mode='Markdown')

    # Investing.com 크롤링
    results = parse_investing_search(query)
    
    await status_msg.delete()
    
    if not results:
        await update.message.reply_text(f"❌ '{query}'에 대한 검색 결과를 찾을 수 없거나 서버 통신에 실패했습니다.")
        return

    # 결과 문자열 조립
    reply_text = f"🔎 **'{query}' 검색 결과 (상위 {len(results)}개)**\n\n"
    for idx, res in enumerate(results, 1):
        reply_text += f"{idx}. **{res['name']}** ({res['symbol']})\n"
        reply_text += f"   🏢 {res['exchange']}\n"
        reply_text += f"   🔗 [상세 페이지 열기]({res['link']})\n\n"

    # Markdown 호환 모드로 전송 (링크 등에 최적화)
    await update.message.reply_text(reply_text, parse_mode='Markdown', disable_web_page_preview=True)

if __name__ == '__main__':
    logger.info("텔레그램 주식 검색 봇 시작 준비 중...")
    
    try:
        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        
        # /get 명령어를 처리하도록 핸들러 등록
        app.add_handler(CommandHandler("get", get_stock_info))

        logger.info("봇 폴링(Polling)을 시작합니다. 텔레그램에서 '/get <종목명>' 을 전송해보세요.")
        app.run_polling()
    except Exception as e:
        logger.error(f"봇 실행 실패: {e}")
