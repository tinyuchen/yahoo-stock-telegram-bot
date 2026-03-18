import os
import random
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# 可以自己擴充清單；這裡先放幾檔台股（Yahoo Finance：台股常用 .TW）
DEFAULT_SYMBOLS = "2330.TW,2454.TW,2317.TW,2303.TW,6505.TW,2881.TW,0050.TW"

SYMBOLS = [s.strip() for s in os.getenv("SYMBOLS", DEFAULT_SYMBOLS).split(",") if s.strip()]
TZ = ZoneInfo("Asia/Taipei")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

def pick_random_symbol() -> str:
    # 每次執行「隨機挑一檔」符合題意：監聽 Yahoo 股市的隨機股票:contentReference[oaicite:4]{index=4}
    return random.choice(SYMBOLS)

def fetch_yahoo_quote(symbol: str) -> dict:
    # Yahoo Finance quote endpoint（非官方，但常用且回 JSON）:contentReference[oaicite:5]{index=5}
    url = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; StockBot/1.0)"
    }
    r = requests.get(url, params={"symbols": symbol}, headers=headers, timeout=20)
    r.raise_for_status()
    j = r.json()
    result = j.get("quoteResponse", {}).get("result", [])
    if not result:
        raise RuntimeError(f"No quote result for symbol={symbol}")
    return result[0]

def send_telegram(text: str):
    # Telegram sendMessage API :contentReference[oaicite:6]{index=6}
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
    }
    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()

def main():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise SystemExit("Missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID (set env or GitHub Secrets).")

    symbol = pick_random_symbol()
    q = fetch_yahoo_quote(symbol)

    name = q.get("shortName") or q.get("longName") or symbol
    price = q.get("regularMarketPrice")
    chg = q.get("regularMarketChange")
    chg_pct = q.get("regularMarketChangePercent")
    currency = q.get("currency") or ""
    market_ts = q.get("regularMarketTime")

    if market_ts:
        tpe_time = datetime.fromtimestamp(market_ts, tz=TZ).strftime("%Y-%m-%d %H:%M:%S")
    else:
        tpe_time = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")

    link = f"https://finance.yahoo.com/quote/{symbol}"

    text = (
        "📈 Yahoo 即時股價（每 5 分鐘自動回報）\n"
        f"標的：{name} ({symbol})\n"
        f"價格：{price} {currency}\n"
        f"漲跌：{chg:+.2f}（{chg_pct:+.2f}%）\n"
        f"時間：{tpe_time}（台北）\n"
        f"來源：{link}"
    )

    send_telegram(text)

if __name__ == "__main__":
    main()
