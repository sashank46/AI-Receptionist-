"""
main.py
The FastAPI server Twilio talks to. This is the entire call flow:

  1. Someone calls your Twilio number
  2. Twilio sends a POST to /voice  -> we greet them + start listening
  3. Twilio's built-in speech recognition transcribes what they say and
     POSTs the text to /gather
  4. We hand the transcript to the LLM agent (app/llm_agent.py)
  5. We turn the agent's reply into speech with edge-tts (app/tts.py)
     and tell Twilio to <Play> it, then listen again
  6. Loop continues until the caller says goodbye or hangs up
  7. If a booking was confirmed during the call, we fire a WhatsApp
     confirmation (app/whatsapp.py)

We use Twilio's <Gather input="speech"> for STT instead of raw audio
streaming + local Whisper. This is a deliberate simplification: Twilio's
built-in speech recognition is reliable over real phone-call audio quality
and needs zero extra infrastructure. (You can swap in Whisper later by
recording instead of gathering — mentioned in the README as a stretch goal.)
"""
import json
from fastapi import FastAPI, Request, Form
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from twilio.twiml.voice_response import VoiceResponse, Gather

from app.config import BASE_URL
from app.database import init_db, get_conn
from app.llm_agent import get_agent_reply
from app.tts import text_to_speech_file
from app.whatsapp import send_whatsapp_confirmation

app = FastAPI(title="AI Voice Receptionist")
app.mount("/static", StaticFiles(directory="static"), name="static")

init_db()


# ---------- call state helpers (persisted in SQLite so a restart doesn't lose an in-progress call) ----------

def _load_history(call_sid: str) -> list[dict]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT history_json FROM call_state WHERE call_sid = ?", (call_sid,)
        ).fetchone()
    return json.loads(row["history_json"]) if row else []


def _save_history(call_sid: str, history: list[dict], caller_phone: str = None):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO call_state (call_sid, history_json, caller_phone)
               VALUES (?, ?, ?)
               ON CONFLICT(call_sid) DO UPDATE SET
                 history_json = excluded.history_json,
                 updated_at = CURRENT_TIMESTAMP""",
            (call_sid, json.dumps(history), caller_phone),
        )
        conn.commit()


async def _speak_and_listen(reply_text: str) -> VoiceResponse:
    """Builds the TwiML: play the agent's reply as audio, then listen for the caller's next turn."""
    filename = await text_to_speech_file(reply_text)
    audio_url = f"{BASE_URL}/static/audio/{filename}"

    vr = VoiceResponse()
    gather = Gather(
        input="speech",
        action="/gather",
        method="POST",
        speech_timeout="auto",
        language="en-IN",
    )
    gather.play(audio_url)
    vr.append(gather)

    # If the caller says nothing at all, Twilio falls through here — try once more.
    vr.redirect("/voice-timeout")
    return vr


# ---------- routes ----------

@app.post("/voice")
async def voice(request: Request):
    """First webhook Twilio hits when a call comes in."""
    form = await request.form()
    call_sid = form.get("CallSid")
    caller_phone = form.get("From")

    greeting = "Hi, thanks for calling! How can I help you today — booking an appointment, or a question?"
    _save_history(call_sid, [], caller_phone)

    vr = await _speak_and_listen(greeting)
    return Response(content=str(vr), media_type="application/xml")


@app.post("/gather")
async def gather(request: Request):
    """Hit every time Twilio finishes transcribing what the caller said."""
    form = await request.form()
    call_sid = form.get("CallSid")
    caller_phone = form.get("From")
    speech_text = form.get("SpeechResult", "")

    history = _load_history(call_sid)
    history.append({"role": "user", "content": speech_text})

    reply_text, updated_history, (booking_confirmed, booking_result) = get_agent_reply(history)
    _save_history(call_sid, updated_history, caller_phone)

    if booking_confirmed and booking_result:
        phone_to_notify = booking_result.get("phone") or caller_phone
        send_whatsapp_confirmation(
            phone_to_notify,
            f"✅ Appointment confirmed!\n{booking_result['message']}\nSee you soon!"
        )

    # End the call cleanly if the agent said goodbye
    if any(word in reply_text.lower() for word in ["goodbye", "bye", "have a great day", "take care"]):
        filename = await text_to_speech_file(reply_text)
        vr = VoiceResponse()
        vr.play(f"{BASE_URL}/static/audio/{filename}")
        vr.hangup()
        return Response(content=str(vr), media_type="application/xml")

    vr = await _speak_and_listen(reply_text)
    return Response(content=str(vr), media_type="application/xml")


@app.post("/voice-timeout")
async def voice_timeout():
    """Fallback if the caller doesn't say anything."""
    vr = VoiceResponse()
    gather = Gather(input="speech", action="/gather", method="POST", speech_timeout="auto", language="en-IN")
    gather.say("Sorry, I didn't catch that. Could you say that again?")
    vr.append(gather)
    vr.say("I still didn't hear anything. Goodbye!")
    vr.hangup()
    return Response(content=str(vr), media_type="application/xml")


@app.get("/appointments")
async def list_appointments():
    """Simple JSON endpoint to see all bookings — handy for your demo/viva."""
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM appointments ORDER BY appt_date, appt_time").fetchall()
    return [dict(r) for r in rows]


@app.get("/")
async def health():
    return {"status": "AI Voice Receptionist is running"}
