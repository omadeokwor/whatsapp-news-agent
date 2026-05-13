"""
Daily WhatsApp news + portfolio brief.

Usage:
  python agent.py          # runs once now, then daily at 8 AM
  python agent.py --once   # run once and exit
"""
import argparse
import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def run() -> None:
    from fetcher import get_stock_data, get_news
    from summarizer import build_message
    from messenger import send_whatsapp

    log.info("Fetching stocks...")
    stocks = get_stock_data()

    log.info("Fetching news...")
    news = get_news()

    log.info("Building message...")
    message = build_message(stocks, news)
    print("\n--- MESSAGE PREVIEW ---")
    print(message)
    print("-----------------------\n")

    log.info("Sending WhatsApp message...")
    send_whatsapp(message)
    log.info("Done.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    if args.once:
        run()
        return

    run()
    scheduler = BlockingScheduler()
    scheduler.add_job(run, "cron", hour=8, minute=0, id="daily_brief")
    log.info("Scheduler running — next brief at 8:00 AM. Press Ctrl+C to stop.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Stopped.")


if __name__ == "__main__":
    main()
