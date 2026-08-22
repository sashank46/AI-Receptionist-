"""
tts.py
Converts the agent's text reply into an MP3 file using edge-tts —
Microsoft's free, no-API-key-needed text-to-speech engine. This is what
keeps the whole project at $0 for the voice output piece (ElevenLabs
would cost money; edge-tts sounds close and is free).

The generated file is saved under static/audio/ and served back to Twilio
as a public URL, because Twilio's <Play> verb needs a URL, not raw bytes.
"""
import edge_tts
import uuid
import os

AUDIO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# A natural-sounding Indian-English voice. Full list: `edge-tts --list-voices`
VOICE = "en-IN-NeerjaNeural"


async def text_to_speech_file(text: str) -> str:
    """
    Generates an mp3 for `text` and returns just the filename (not full path),
    so the caller can build a public URL like f"{BASE_URL}/static/audio/{filename}".
    """
    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(AUDIO_DIR, filename)
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(filepath)
    return filename
