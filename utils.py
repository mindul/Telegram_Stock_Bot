import FinanceDataReader as fdr
import logging

logger = logging.getLogger(__name__)

def parse_investing_search(query: str) -> list:
    """
    FinanceDataReader를 사용하여 종목 정보를 검색합니다.
    차단 위험이 있는 Investing.com 스크래핑의 완벽한 대안입니다.
    """
    try:
        # 한국 거래소(KRX) 전체 종목 리스트를 가져옵니다 (상장사 전체)
        # 이 데이터는 메모리에 캐싱하거나 전역 변수로 관리하면 더 빠릅니다.
        df_krx = fdr.StockListing('KRX')

        # 입력한 쿼리가 종목명 또는 종목코드에 포함된 데이터 필터링
        # 이름(Name) 또는 코드(Code)에서 검색어 포함 여부 확인
        matched = df_krx[df_krx['Name'].str.contains(query, case=False) | 
                         df_krx['Code'].str.contains(query, case=False)]

        if matched.empty:
            return []

        results = []
        # 검색 결과 중 상위 3개만 추출
        for _, row in matched.head(3).iterrows():
            symbol = row['Code']
            name = row['Name']
            market = row['Market']  # KOSPI, KOSDAQ 등
            
            # 네이버 금융 등 표준 상세 페이지 링크로 대체 (Investing.com 대체)
            link = f"https://finance.naver.com/item/main.naver?code={symbol}"

            results.append({
                "name": name,
                "symbol": symbol,
                "exchange": market,
                "link": link
            })

        return results

    except Exception as e:
        logger.error(f"FinanceDataReader 검색 중 오류 발생: {e}")
        # None을 반환하여 bot.py에서 서버 오류 메시지를 띄우게 함
        return None

def split_message(message: str, max_length: int = 4000) -> list:
    """메시지가 너무 길 경우 분할"""
    return [message[i:i + max_length] for i in range(0, len(message), max_length)]