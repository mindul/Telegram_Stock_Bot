import FinanceDataReader as fdr
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# 주식 데이터 캐싱을 위한 전역 변수
_cached_stock_df = None

def get_stock_listing():
    """
    국내(KRX)와 미국(NASDAQ, NYSE, AMEX) 종목 리스트를 가져와 
    하나의 통합 데이터프레임으로 만들어 캐싱 및 반환합니다.
    """
    global _cached_stock_df
    if _cached_stock_df is not None:
        return _cached_stock_df
        
    try:
        logger.info("최초 주식 목록 데이터를 가져옵니다. (KRX, NASDAQ, NYSE, AMEX)...")
        
        # 국내 주식
        df_krx = fdr.StockListing('KRX')
        
        # 미국 주식
        df_nasdaq = fdr.StockListing('NASDAQ')
        df_nyse = fdr.StockListing('NYSE')
        df_amex = fdr.StockListing('AMEX')
        
        # 미국 주식은 종목코드 컬럼명이 'Symbol' 일 수 있으므로 'Code'로 통일
        for df, market_name in [(df_nasdaq, 'NASDAQ'), (df_nyse, 'NYSE'), (df_amex, 'AMEX')]:
            if 'Symbol' in df.columns and 'Code' not in df.columns:
                df.rename(columns={'Symbol': 'Code'}, inplace=True)
            # Market 컬럼 명시적 추가 (없는 경우를 방지)
            if 'Market' not in df.columns:
                df['Market'] = market_name
        
        # 데이터프레임 합치기
        _cached_stock_df = pd.concat([df_krx, df_nasdaq, df_nyse, df_amex], ignore_index=True)
        
        logger.info(f"주식 목록 데이터 병합 및 캐싱 완료 (총 {_cached_stock_df.shape[0]}종목).")
        return _cached_stock_df
        
    except Exception as e:
        logger.error(f"주식 목록 로드 중 오류 발생: {e}")
        return None

def parse_investing_search(query: str) -> list:
    """
    FinanceDataReader를 사용하여 종목 정보를 검색합니다.
    차단 위험이 있는 Investing.com 스크래핑의 완벽한 대안입니다.
    """
    try:
        # 캐싱된 전체 데이터프레임 가져오기 (없으면 최초 로드)
        df_all = get_stock_listing()
        
        if df_all is None or df_all.empty:
            return []

        # 입력한 쿼리가 종목명 또는 종목코드에 포함된 데이터 필터링 (대소문자 구분 없음)
        matched = df_all[
            df_all['Name'].str.contains(query, case=False, na=False) | 
            df_all['Code'].str.contains(query, case=False, na=False)
        ]

        if matched.empty:
            return []

        results = []
        # 검색 결과 중 상위 5개 추출 (검색 범위가 확장되었으므로 상위 5개)
        for _, row in matched.head(5).iterrows():
            symbol = str(row['Code'])
            name = str(row['Name'])
            market = str(row.get('Market', 'Unknown'))
            
            # 주식 시장 구분에 따른 링크(네이버 vs 야후 파이낸스)
            if market in ['KOSPI', 'KOSDAQ', 'KONEX']:
                link = f"https://finance.naver.com/item/main.naver?code={symbol}"
            else:
                # 미국 주식(NASDAQ, NYSE, AMEX 등)의 경우 야후 파이낸스
                link = f"https://finance.yahoo.com/quote/{symbol}"

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
    """FinanceDataReader를 활용하여 주요 환율(USD, AUD, JPY)을 가져옵니다."""
    try:
        rates = {}
        
        # USD/KRW
        df_usd = fdr.DataReader('USDKRW=X')
        if not df_usd.empty:
            rates['USD'] = f"🇺🇸 USD: {df_usd.iloc[-1]['Close']:,.2f} 원"
            
        # AUD/KRW
        df_aud = fdr.DataReader('AUDKRW=X')
        if not df_aud.empty:
            rates['AUD'] = f"🇦🇺 AUD: {df_aud.iloc[-1]['Close']:,.2f} 원"
            
        # JPY/KRW (FDR에서는 1엔 기준으로 나옴. 대중적인 100엔 기준으로 변환 표기)
        df_jpy = fdr.DataReader('JPYKRW=X')
        if not df_jpy.empty:
            rates['JPY'] = f"🇯🇵 JPY: {df_jpy.iloc[-1]['Close']*100:,.2f} 원 (100엔 기준)"
            
        return rates
    except Exception as e:
        logger.error(f"환율 정보를 가져오는 중 오류 발생: {e}")
        return {}