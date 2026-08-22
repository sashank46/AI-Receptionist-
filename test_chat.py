"""
test_chat.py
Test the AI receptionist's BRAIN (the LLM agent + booking logic) directly
in your terminal — no Twilio account, no phone call, no ngrok needed.

This is the fastest way to check your OPENAI_API_KEY works and the
conversation/booking logic behaves correctly, before wiring up the phone.

Run:
    python test_chat.py
"""
import sys
from app.database import init_db
from app.llm_agent import get_agent_reply

init_db()


def main():
    print("=" * 60)
    print("AI Voice Receptionist — text chat tester")
    print("(type 'quit' to exit)")
    print("=" * 60)

    history = []
    first_message = "Hi, thanks for calling! How can I help you today — booking an appointment, or a question?"
    print(f"\nAgent: {first_message}")
    history.append({"role": "assistant", "content": first_message})

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break

        history.append({"role": "user", "content": user_input})
        reply_text, history, (booking_confirmed, booking_result) = get_agent_reply(history)

        print(f"\nAgent: {reply_text}")
        if booking_confirmed:
            print(f"\n[SYSTEM] Booking confirmed! {booking_result}")
            print("[SYSTEM] In a real call, a WhatsApp confirmation would be sent now.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
