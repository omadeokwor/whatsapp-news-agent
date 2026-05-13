"""
Send a WhatsApp message via Twilio.
"""
import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()


def send_whatsapp(message: str) -> None:
    client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
    client.messages.create(
        from_=f"whatsapp:{os.environ['TWILIO_FROM']}",
        to=f"whatsapp:{os.environ['TWILIO_TO']}",
        body=message,
    )
    print("[messenger] WhatsApp message sent.")
