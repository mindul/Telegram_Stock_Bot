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

def get_exchange_rates() -> dict:
    """네이버를 스크래핑하여 미국달러, 호주달러, 일본엔화 환율을 가져옵니다."""
    import requests
    from bs4 import BeautifulSoup
    
    rates = {}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        # (1) 호주달러 환율
        aus_url = 'https://search.naver.com/search.naver?query=%ED%98%B8%EC%A3%BC%EB%8B%AC%EB%9F%AC+%ED%99%98%EC%9C%A8'
        response = requests.get(aus_url, headers=headers)
        dom = BeautifulSoup(response.content, "html.parser")
        aus_price = dom.select_one(".price")
        aus_gap = dom.select_one(".price_gap")
        rates['AUD'] = f"> 🇦🇺 AUD $ {aus_price.text}원, {aus_gap.text}" if aus_price and aus_gap else "> 🇦🇺 AUD 환율 정보 없음"
        
        # (2) 달러 환율
        usd_url = 'https://search.naver.com/search.naver?query=%EB%8B%AC%EB%9F%AC+%ED%99%98%EC%9C%A8'
        response = requests.get(usd_url, headers=headers)
        dom = BeautifulSoup(response.content, "html.parser")
        usd_price = dom.select_one(".price")
        usd_gap = dom.select_one(".price_gap")
        rates['USD'] = f"> 🇺🇸 USD $ {usd_price.text}원, {usd_gap.text}" if usd_price and usd_gap else "> 🇺🇸 USD 환율 정보 없음"

        # (3) 엔 환율
        jpn_url = 'https://search.naver.com/search.naver?query=%EC%97%94+%ED%99%98%EC%9C%A8'
        response = requests.get(jpn_url, headers=headers)
        dom = BeautifulSoup(response.content, "html.parser")
        jpn_price = dom.select_one(".price")
        jpn_gap = dom.select_one(".price_gap")
        rates['JPY'] = f"> 🇯🇵 JPY ¥ {jpn_price.text}원, {jpn_gap.text}" if jpn_price and jpn_gap else "> 🇯🇵 JPY 환율 정보 없음"
        
        return rates

    except Exception as e:
        logger.error(f"환율 정보 스크래핑 중 오류: {e}")
        return None