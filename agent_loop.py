"""
True agentic WhatsApp brief — Gemini decides what tools to call and when.

Instead of a fixed pipeline (fetch → summarize → send), Gemini is given tools
and a goal, then runs its own reasoning loop until the message is sent.

Usage:
  python agent_loop.py          # runs once now, then daily at 8 AM
  python agent_loop.py --once   # run once and exit
"""
import argparse
import logging
import os

from google import genai
from google.genai import types
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# _GOAL is the system instruction — it tells Gemini who it is and what it needs
# to accomplish. It does NOT tell Gemini how to do it step by step; Gemini
# figures that out itself using the tools available to it.
_GOAL = """
You are Omade's personal daily briefing agent. You will be given a research summary
containing stock prices and news. Your job:
1. Compose a casual, punchy WhatsApp message (under 1200 characters) using WhatsApp
   bold (*bold*) with these sections:
   - Opening line: "THIS IS OMADE'S AUTOMATED CHATBOT HEHEHEEH 🤖"
   - Fun personalised greeting
   - *📈 Stocks* — each ticker on its own line with price and % change (▲ or ▼)
   - *🎤 Beyoncé* — 1-2 sentence summary
   - *🤖 AI News* — 1-2 sentence summary
   - *🇳🇬 Nigerian Fun Fact* — one surprising fact
   - Fun sign-off
2. If Google stock is doing well, sneak a joke about it into the greeting or sign-off.
3. Send the message via WhatsApp using the send_whatsapp_message tool.
"""


# ── Tool implementations ──────────────────────────────────────────────────────

def send_whatsapp_message(message: str) -> str:
    """Send the composed WhatsApp message to Omade.

    Args:
        message: The complete formatted WhatsApp message to send.
    """
    # This is a real Python function — when Gemini decides the message is ready,
    # it calls this tool and passes in the message it composed. We then actually
    # send it via Twilio. Gemini never touches Twilio directly — it just calls
    # this function and trusts us to handle the delivery.
    from messenger import send_whatsapp
    print("\n--- MESSAGE PREVIEW ---")
    print(message)
    print("-----------------------\n")
    send_whatsapp(message)
    log.info("WhatsApp message sent.")
    return "Message sent successfully."


# ── Tool registry ─────────────────────────────────────────────────────────────

# _PYTHON_TOOLS is the list of Python functions we expose to Gemini as tools.
# Gemini reads the docstring and type hints on each function to understand
# what it does and how to call it. At runtime, Gemini decides whether to call
# any of these — we never hardcode which ones get called or in what order.
_PYTHON_TOOLS = [send_whatsapp_message]

# _TOOL_MAP lets us look up a function by name (the name Gemini uses in its
# function_call response) so we can execute it when Gemini requests it.
_TOOL_MAP = {fn.__name__: fn for fn in _PYTHON_TOOLS}


def run() -> None:
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    # ── Phase 1: Web research via Google Search ───────────────────────────────
    # Gemini's built-in Google Search tool cannot be combined with function
    # calling in the same request (API limitation). So we do all web research
    # first in a standalone call, then pass the results into Phase 2.
    log.info("Phase 1: searching the web for news...")
    search_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=(
            "Search for and summarise: "
            "1) current stock prices and today's % change for: GOOG, NVDA, VFV.TO, QQC, "
            "2) the latest Beyoncé news, "
            "3) the latest AI news, "
            "4) one surprising Nigerian fun fact (history, culture, food, or language). "
            "Return a short plain-text summary for each."
        ),
        config=types.GenerateContentConfig(
            # google_search is a built-in Gemini tool — Gemini handles the
            # actual search calls internally and returns grounded results as text.
            # We don't see or control the individual searches; we just get the summary.
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )
    # search_response.text is a plain-text summary of everything Gemini found.
    # We carry this into Phase 2 as context for composing the message.
    news_summary = search_response.text
    log.info("Web research complete.")

    # ── Phase 2: Compose and send via function calling ────────────────────────
    # Now we start a chat session with our Python tools available. Gemini is
    # given the news summary and told to compose and send the WhatsApp message.
    # It will decide on its own to call send_whatsapp_message when it's ready.
    log.info("Phase 2: composing and sending brief...")
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            tools=_PYTHON_TOOLS,         # hand Gemini our Python toolbox
            system_instruction=_GOAL,    # tell Gemini its role and message format
        ),
    )

    # Kick off the conversation by giving Gemini the research summary.
    # From here, Gemini is in control — it decides what to do next.
    response = chat.send_message(
        f"Here is today's news summary from web research:\n\n{news_summary}\n\n"
        "Now compose the WhatsApp message using this data and send it."
    )

    # ── Agent reasoning loop ──────────────────────────────────────────────────
    # Each iteration of this loop is one "turn" in the conversation.
    # Gemini responds, we check if it wants to call any tools, run them,
    # and send the results back. This repeats until Gemini stops calling tools,
    # which means it considers the task complete.
    while True:
        # A Gemini response is made up of "parts". Each part is either text
        # or a function_call. We filter for function calls here — those are
        # the actions Gemini has decided to take based on its reasoning.
        fn_calls = [
            part.function_call
            for part in response.candidates[0].content.parts
            if part.function_call and part.function_call.name
        ]

        # No function calls means Gemini has finished reasoning and acting.
        # It may have produced a final text response, but the job is done.
        if not fn_calls:
            log.info("Agent finished.")
            break

        # Execute every function Gemini requested and collect the results.
        # Gemini can request multiple tool calls in a single turn, so we
        # handle them all before sending anything back.
        fn_responses = []
        for fc in fn_calls:
            name = fc.name          # the function Gemini wants to call
            args = dict(fc.args)    # the arguments Gemini chose to pass in
            log.info("Tool call: %s(%s)", name, args)

            # Look up the real Python function by name and call it.
            # This is where the actual work happens — Gemini made a decision,
            # and we're carrying it out in Python.
            result = _TOOL_MAP[name](**args)

            # Package the result as a FunctionResponse part so Gemini can
            # read it in the next turn and continue its reasoning.
            fn_responses.append(
                types.Part.from_function_response(
                    name=name,
                    response={"result": result},
                )
            )

        # Send all tool results back to Gemini in one message.
        # Gemini will read these results and decide what to do next —
        # either call more tools or wrap up.
        response = chat.send_message(fn_responses)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    if args.once:
        run()
        return

    # Run once immediately, then schedule to run every day at 8 AM
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
