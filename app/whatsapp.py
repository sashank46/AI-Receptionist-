"""
whatsapp.py
Sends a WhatsApp confirmation message after a successful booking, using
Twilio's free WhatsApp Sandbox. No WhatsApp Business API approval needed
for a capstone demo — the recipient just has to "join" your sandbox once
(one-time WhatsApp message, explained in the README).
"""
from twilio.rest import Client
from app.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER


def send_whatsapp_confirmation(to_phone: str, message: str) -> bool:
    """
    to_phone must be in E.164 format, e.g. +919876543210.
    Returns True/False instead of raising, so a WhatsApp failure never
    breaks the phone call flow — the call itself already confirmed verbally.
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("[whatsapp] Twilio credentials missing — skipping WhatsApp send.")
        return False

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=f"whatsapp:{to_phone}",
            body=message,
        )
        return True
    except Exception as e:
        print(f"[whatsapp] Failed to send confirmation: {e}")
        return False
