import FinanceDataReader as fdr
import pandas as pd
import requests
import logging

logger = logging.getLogger(__name__)

# 주식 데이터 캐싱을 위한 전역 변수
_cached_krx_df = None

def get_krx_listing():
    """
    국내(KRX) 종목 리스트만 가져와 캐싱합니다.
    해외 주식은 빠르고 정확한 야후 파이낸스 자체 검색 API를 활용합니다.
    """
    global _cached_krx_df
    if _cached_krx_df is not None:
        return _cached_krx_df
        
    try:
        logger.info("최초 국내 주식 목록 데이터를 가져옵니다. (KRX)...")
        # 국내 주식
        _cached_krx_df = fdr.StockListing('KRX')
        
        # NaN 처리 (str.contains 시 에러 방지)
        _cached_krx_df['Name'] = _cached_krx_df['Name'].fillna('')
        _cached_krx_df['Code'] = _cached_krx_df['Code'].fillna('')
        
        logger.info(f"국내 주식 목록 캐싱 완료 (총 {_cached_krx_df.shape[0]}종목).")
        return _cached_krx_df
        
    except Exception as e:
        logger.error(f"국내 주식 목록 로드 중 오류 발생: {e}")
        return None

def search_yahoo_finance(query: str) -> list:
    """야후 파이낸스 검색 API를 사용하여 해외 주식을 검색합니다."""
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    results = []
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status()
        data = res.json()
        quotes = data.get('quotes', [])
        
        for q in quotes:
            # 주식(EQUITY)이나 ETF만 가져오기
            if q.get('quoteType') not in ['EQUITY', 'ETF']: continue
            
            symbol = q.get('symbol', 'Unknown')
            name = q.get('shortname') or q.get('longname') or 'Unknown'
            market = q.get('exchDisp', 'Unknown')
            
            link = f"https://finance.yahoo.com/quote/{symbol}"
            results.append({
                "name": name,
                "symbol": symbol,
                "exchange": market,
                "link": link
            })
            if len(results) >= 5:
                break
        return results
    except Exception as e:
        logger.error(f"야후 파이낸스 검색 오류: {e}")
        return []

def parse_investing_search(query: str) -> list:
    """
    국내 주식은 FDR 캐시에서, 해외 주식은 야후 파이낸스 API에서 검색하여 통합 검색 결과를 제공합니다.
    """
    results = []
    seen_symbols = set()

    try:
        # 1. 국내 주식 검색 (캐싱된 KRX 데이터프레임)
        df_krx = get_krx_listing()
        if df_krx is not None and not df_krx.empty:
            # 대소문자 구분 없이 검색
            matched = df_krx[
                df_krx['Name'].str.contains(query, case=False, na=False) | 
                df_krx['Code'].str.contains(query, case=False, na=False)
            ]
            
            for _, row in matched.head(5).iterrows():
                symbol = str(row['Code'])
                name = str(row['Name'])
                market = str(row.get('Market', 'KRX'))
                
                link = f"https://finance.naver.com/item/main.naver?code={symbol}"
                results.append({
                    "name": name,
                    "symbol": symbol,
                    "exchange": market,
                    "link": link
                })
                # 야후 결과와 중복 방지 (야후는 한국 주식 뒤에 .KS / .KQ가 붙음)
                seen_symbols.add(symbol)
                seen_symbols.add(symbol + '.KS')
                seen_symbols.add(symbol + '.KQ')

        # 2. 해외 주식 검색 (야후 파이낸스 실시간 API)
        yahoo_results = search_yahoo_finance(query)
        
        for yr in yahoo_results:
            if yr['symbol'] not in seen_symbols:
                results.append(yr)
                seen_symbols.add(yr['symbol'])
                
        # 검색 결과 상위 7개로 제한
        return results[:7]

    except Exception as e:
        logger.error(f"통합 검색 중 오류 발생: {e}")
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