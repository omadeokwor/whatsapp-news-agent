# Omade's WhatsApp News Agent 🤖

A daily automated WhatsApp brief that sends you stocks, Beyoncé news, AI news, and a Nigerian fun fact every morning at 8 AM.

## What it sends

- **📈 Stocks** — live prices and % change for your portfolio tickers
- **🎤 Beyoncé** — latest news from Queen Bey's world
- **🤖 AI News** — what's happening in artificial intelligence
- **🇳🇬 Nigerian Fun Fact** — a fresh daily fact about Nigeria

## Requirements

- Python 3.10+
- [OpenAI API key](https://platform.openai.com/) — for the default agent
- [Google Gemini API key](https://aistudio.google.com/) — for the Gemini variant
- [NewsAPI key](https://newsapi.org/)
- [Twilio account](https://www.twilio.com/) with WhatsApp sandbox enabled

## Setup

1. Clone the repo and create a virtual environment:

```bash
git clone https://github.com/omadeokwor/whatsapp-news-agent.git
cd whatsapp-news-agent
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key (used by `agent.py`) |
| `GEMINI_API_KEY` | Your Google Gemini API key (used by `agent_genai.py`) |
| `NEWS_API_KEY` | Your NewsAPI key |
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_FROM` | Twilio WhatsApp sandbox number |
| `TWILIO_TO` | Your WhatsApp number |
| `TICKERS` | Comma-separated stock tickers (e.g. `GOOG,NVDA`) |
| `NEWS_TOPICS` | Comma-separated news topics (e.g. `Beyonce,artificial intelligence`) |

## Usage

There are two variants — one powered by OpenAI and one by Google Gemini. They behave identically; pick whichever API key you have.

**OpenAI variant:**
```bash
python agent.py --once      # run once (for testing)
python agent.py             # run on a schedule (sends daily at 8 AM)
```

**Gemini variant:**
```bash
python agent_genai.py --once
python agent_genai.py
```
