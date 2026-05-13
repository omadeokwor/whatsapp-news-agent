"""
Fetch stock prices and news headlines.
"""
import os
import requests
import yfinance as yf
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


def get_stock_data() -> list[dict]:
    tickers = [t.strip() for t in os.environ.get("TICKERS", "GOOG,NVDA").split(",")]
    results = []
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).fast_info
            price = info.last_price
            prev = info.previous_close
            change_pct = ((price - prev) / prev) * 100
            display = ticker.replace(".TO", "").replace("-F", "")
            results.append({"ticker": display, "price": price, "change_pct": change_pct})
        except Exception as e:
            print(f"[fetcher] Could not fetch {ticker}: {e}")
    return results


def get_news() -> list[dict]:
    api_key = os.environ["NEWS_API_KEY"]
    topics = [t.strip() for t in os.environ.get("NEWS_TOPICS", "").split(",") if t.strip()]
    since = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    results = []

    for topic in topics:
        try:
            resp = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q": topic,
                    "apiKey": api_key,
                    "pageSize": 3,
                    "sortBy": "publishedAt",
                    "from": since,
                    "language": "en",
                },
                timeout=10,
            )
            articles = resp.json().get("articles", [])
            if articles:
                results.append({
                    "topic": topic,
                    "headlines": [a["title"] for a in articles[:3]],
                })
        except Exception as e:
            print(f"[fetcher] News error for '{topic}': {e}")

    return results
