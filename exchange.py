import requests
from bs4 import BeautifulSoup
import urllib.parse
import urllib3
import datetime

urllib3.disable_warnings()
http = urllib3.PoolManager()

# Telegram URL (@Daebakrobot bot)
Teleg_URL = "https://api.telegram.org/bot277784269:AAGWKMdIZB165_9Gi1GMYsvTx67BlpOeyd4/sendMessage?chat_id=65875188&text="

# 텔레그램으로 알람 보내기(호주달러, 미국달러, 일본엔)
def SendTelegram(aus, usd, jpn):
    now = datetime.datetime.now()
    now_format = now.strftime('%m월 %d일 %H시 %M분')
    strTelMsg = '{}{}{}{}{}{}'.format(Teleg_URL,
    urllib.parse.quote("<오늘의 환율 정보>\n"),
    urllib.parse.quote("("+now_format+")\n"),
    urllib.parse.quote(aus),urllib.parse.quote(usd),
    urllib.parse.quote(jpn))
    http.request('GET', strTelMsg).data

# (1) 호주달러 환율
aus_url = 'https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&query=%ED%98%B8%EC%A3%BC%EB%8B%AC%EB%9F%AC+%ED%99%98%EC%9C%A8&oquery=%ED%98%B8%EC%A3%BC%EB%8B%AC%EB%9F%AC+%ED%99%98%EC%9C%A8&tqi=ijCQesqVOZossS82zoGssssssE0-047285'
response = requests.get(aus_url)
dom1 = BeautifulSoup(response.content, "html.parser")
aus_price = dom1.select_one(".price")
aus_gap = dom1.select_one(".price_gap")
aus_str = f"> AUD$ {aus_price.text}원, {aus_gap.text}\n"

# (2) 달러 환율
usd_url = 'https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&query=%EB%8B%AC%EB%9F%AC+%ED%99%98%EC%9C%A8&oquery=%ED%98%B8%EC%A3%BC%EB%8B%AC%EB%9F%AC+%ED%99%98%EC%9C%A8&tqi=ijCxbsqVN8ossm7j%2F84ssssstZw-328487'
response = requests.get(usd_url)
dom2 = BeautifulSoup(response.content, "html.parser")
usd_price = dom2.select_one(".price")
usd_gap = dom2.select_one(".price_gap")  # Corrected to use dom2
usd_str = f"> $ {usd_price.text}원, {usd_gap.text}\n"

# (3) 엔 환율
jpn_url = 'https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&query=%EC%97%94+%ED%99%98%EC%9C%A8&oquery=%EB%8B%AC%EB%9F%AC+%ED%99%98%EC%9C%A8&tqi=ijC0ZsqVOsossNHn9gGssssst8N-477066'
response = requests.get(jpn_url)
dom3 = BeautifulSoup(response.content, "html.parser")
jpn_price = dom3.select_one(".price")
jpn_gap = dom3.select_one(".price_gap")  # Corrected to use dom2
jpn_str = f"> Y {jpn_price.text}원, {jpn_gap.text}\n"

# (4) 대만달러 환율
twd_url = 'https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query=%EB%8C%80%EB%A7%8C%EB%8B%AC%EB%9F%AC+%ED%99%98%EC%9C%A8'
response = requests.get(twd_url)
dom4 = BeautifulSoup(response.content, "html.parser")
twd_price = dom4.select_one(".price")
twd_gap = dom4.select_one(".price_gap")  # Corrected to use dom2
twd_str = f"> TWD {twd_price.text}원, {twd_gap.text}"

# 텔레그램 발사!
SendTelegram(aus_str, usd_str, jpn_str)  # Launch telegram!