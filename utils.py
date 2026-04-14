import httpx
from bs4 import BeautifulSoup
import re

def parse_investing_search(query: str) -> list:
    """Investing.com에서 종목 코드를 검색하여 결과(종목명, 심볼, URL) 리스트를 반환합니다."""
    url = f"https://kr.investing.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0"
    }
    
    try:
        response = httpx.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        
        # <a> 태그를 순회하며 주식(equities) 링크 파싱
        for a in soup.find_all("a"):
            href = a.get("href", "")
            
            # 주식 관련 종목이고, 보통 뉴스 기사가 아닌 경우 추출 (/equities/...)
            if href.startswith("/equities/"):
                text_lines = [line.strip() for line in a.text.split("\n") if line.strip()]
                
                # ['AAPL', '애플', '주식 - 나스닥', 'equities'] 형태를 파싱
                if len(text_lines) >= 3:
                    symbol = text_lines[0]
                    name = text_lines[1]
                    exchange = text_lines[2]
                    
                    full_link = "https://kr.investing.com" + href
                    
                    # 이미 추가한 링크는 중복 방지
                    if any(r['link'] == full_link for r in results):
                        continue
                        
                    results.append({
                        "name": name,
                        "symbol": symbol,
                        "exchange": exchange,
                        "link": full_link
                    })
                    
            if len(results) >= 3: # 상위 3개까지만
                break
                
        return results
        
    except Exception as e:
        print(f"Error fetching investing.com: {e}")
        return []

def split_message(message: str, max_length: int = 4000) -> list:
    """메시지가 너무 길 경우 분할 (이전 하위 호환을 위해 남겨둠)"""
    return [message[i:i + max_length] for i in range(0, len(message), max_length)]
