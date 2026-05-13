"""
Use OpenAI to turn raw stock + news data into a punchy WhatsApp message.
"""
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = OpenAI()

_PROMPT = """You are writing a daily WhatsApp brief for one person. Make it casual, punchy, and fun.
Use WhatsApp bold formatting (*bold*) for headers. Keep the whole message under 1200 characters.

STOCKS:
{stocks}

NEWS:
{news}

Format:
- Start with exactly this line: "THIS IS OMADE'S AUTOMATED CHATBOT HEHEHEEH 🤖"
- GreetingS — make it fun and personal.
- *📈 Stocks* section: each stock on its own line with price and % change (use ▲ or ▼)
- *🎤 Beyoncé* section: 1-2 sentence summary of what's happening in her world
- *🤖 AI News* section: 1-2 sentence summary of the latest in artificial intelligence
- *🇳🇬 Nigerian Fun Fact* section: one surprising, interesting, or funny fact about Nigeria (history, culture, food, language, people — keep it fresh and educational)
- Sign off with a fun line"""


def build_message(stocks: list[dict], news: list[dict]) -> str:
    stocks_text = "\n".join(
        f"{s['ticker']}: ${s['price']:.2f} "
        f"({'+'if s['change_pct'] >= 0 else ''}{s['change_pct']:.2f}%)"
        for s in stocks
    )
    news_text = "\n\n".join(
        f"{n['topic'].upper()}:\n" + "\n".join(f"- {h}" for h in n["headlines"])
        for n in news
    )

    resp = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": _PROMPT.format(stocks=stocks_text, news=news_text),
            }
        ],
        max_tokens=500,
        temperature=0.7,
    )
    return resp.choices[0].message.content
