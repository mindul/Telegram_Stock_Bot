import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

from config import TELEGRAM_BOT_TOKEN, ADMIN_USER_ID
from utils import parse_investing_search, get_exchange_rates

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def get_stock_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/get 명령어 핸들러: 종목을 검색하고 결과를 회신합니다."""
    user_id = update.effective_user.id

    # 1. 명령어 파라미터 체크
    if not context.args:
        await update.message.reply_text(
            "검색할 종목명이나 코드를 입력해주세요. \n예시: `/get AAPL` 또는 `/get 삼성전기`", 
            parse_mode='Markdown'
        )
        return

    query = " ".join(context.args)
    logger.info(f"사용자({user_id}) 종목 검색 요청: {query}")

    # 2. 권한 검사
    # if user_id != ADMIN_USER_ID:
    #     logger.warning(f"권한 없는 사용자({user_id}) 접근 시도 차단.")
    #     await update.message.reply_text(f"⛔️ 접근 권한이 없습니다. (ID: {user_id})")
    #     return

    # 3. 진행 상태 알림
    status_msg = await update.message.reply_text(f"⏳ **'{query}'** 종목을 검색 중입니다...", parse_mode='Markdown')

    try:
        # 4. Investing.com 크롤링 호출 (utils.py)
        results = parse_investing_search(query)

        # 상태 메시지 삭제
        await status_msg.delete()

        # 5. 결과 처리
        if results is None:
            # 서버 차단(403) 또는 통신 에러 발생 시
            await update.message.reply_text(
                f"❌ 서버 응답 오류가 발생했습니다.\n현재 Investing.com 접속이 차단되었거나 점검 중일 수 있습니다. 잠시 후 다시 시도해주세요."
            )
            return

        if not results:
            # 검색 결과가 실제로 없는 경우
            await update.message.reply_text(f"❓ '{query}'에 대한 검색 결과를 찾을 수 없습니다.")
            return

        # 6. 결과 메시지 조립
        reply_text = f"🔎 **'{query}' 검색 결과 (상위 {len(results)}개)**\n\n"
        for idx, res in enumerate(results, 1):
            reply_text += f"{idx}. **{res['name']}** ({res['symbol']})\n"
            reply_text += f"   🏢 {res['exchange']}\n"
            reply_text += f"   🔗 [상세 페이지 열기]({res['link']})\n\n"

        # 7. 최종 결과 전송
        await update.message.reply_text(
            reply_text, 
            parse_mode='Markdown', 
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"오류 발생: {e}")
        # 오류 발생 시 사용자에게 알림 (상태 메시지가 아직 있다면 삭제)
        try:
            await status_msg.delete()
        except:
            pass
        await update.message.reply_text("⚠️ 봇 처리 중 예상치 못한 오류가 발생했습니다.")

async def get_rate_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/rate 명령어 핸들러: 네이버/FDR에서 주요 환율 정보를 가져옵니다."""
    user_id = update.effective_user.id

    # 1. 권한 검사 주석 처리 유지 (필요에 따라 해제 가능)
    # if user_id != ADMIN_USER_ID:
    #     logger.warning(f"권한 없는 사용자({user_id}) (환율검색) 접근 시도 차단.")
    #     await update.message.reply_text(f"⛔️ 접근 권한이 없습니다. (ID: {user_id})")
    #     return

    status_msg = await update.message.reply_text("⏳ 실시간 환율 정보를 가져오는 중입니다...")

    try:
        rates = get_exchange_rates()
        await status_msg.delete()

        if not rates:
            await update.message.reply_text("❌ 환율 정보를 가져오는 데 실패했습니다.")
            return

        reply_text = f"💱 **오늘의 주요 환율 정보**\n\n"
        reply_text += rates.get('USD', '') + "\n"
        reply_text += rates.get('AUD', '') + "\n"
        reply_text += rates.get('JPY', '') + "\n"

        await update.message.reply_text(reply_text)

    except Exception as e:
        logger.error(f"환율 오류 발생: {e}")
        try:
            await status_msg.delete()
        except:
            pass
        await update.message.reply_text("⚠️ 환율 정보를 가져오는 중 오류가 발생했습니다.")

async def get_help_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/? 또는 /h 명령어 핸들러: help.md 파일의 내용을 읽어 보여줍니다."""
    try:
        with open('help.md', 'r', encoding='utf-8') as f:
            help_text = f.read()
        await update.message.reply_text(help_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"도움말 읽기 오류 발생: {e}")
        await update.message.reply_text("⚠️ 도움말 정보를 가져오는 중 오류가 발생했습니다.")

if __name__ == '__main__':
    logger.info("텔레그램 주식 검색 봇 시작 준비 중...")

    try:
        # 애플리케이션 빌드
        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

        # /get 명령어 핸들러 등록
        app.add_handler(CommandHandler("get", get_stock_info))
        # /rate 명령어 핸들러 등록
        app.add_handler(CommandHandler("rate", get_rate_info))
        # /? 및 /h 명령어 핸들러 등록
        app.add_handler(CommandHandler(["h", "?"], get_help_info))

        logger.info("봇 폴링(Polling)을 시작합니다. 텔레그램에서 '/get <종목명>'을 전송해보세요.")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"봇 실행 실패: {e}")