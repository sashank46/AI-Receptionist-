# 📞 AI Voice Receptionist & Appointment Booking Agent

An intelligent, zero-cost-tier **AI Phone Receptionist** designed for small businesses (clinics, salons, consultancies, etc.). It answers incoming phone calls, conducts natural speech conversations, checks real-time appointment availability, books slots in a database, and sends instant WhatsApp confirmations to callers — all powered by free-tier APIs and open tools.

---

## 🌟 Key Features

- 🗣️ **Conversational Phone Interface**: Integrated with Twilio Voice & speech recognition (telephony-optimized ASR).
- 🧠 **Smart LLM Tool Calling**: Uses Groq (`llama-3.3-70b-versatile`) or OpenAI (`gpt-4o-mini`) function calling to query business info, check real slot availability, and execute bookings.
- 🔊 **Natural Text-to-Speech (TTS)**: Instant, realistic voice response powered by Microsoft `edge-tts` (`en-IN-NeerjaNeural`).
- 📅 **Dynamic Availability & Persistence**: Real-time SQLite slot management with per-call conversation state persistence (`appointments.db`).
- 💬 **Instant WhatsApp Confirmations**: Automatic post-booking confirmation messages sent via Twilio WhatsApp Sandbox.
- 🧪 **Interactive Terminal Tester**: Test the AI agent's brain locally without spending any credits or connecting phone lines (`test_chat.py`).

---

## 🏗️ Architecture & Call Flow

```
 Caller 📱
    │
    ▼ (Inbound Phone Call)
 Twilio Voice Service
    │
    ├─► 1. Transcribes voice input (Telephony ASR)
    │
    ▼ (HTTP POST /voice or /gather)
 FastAPI Application Server (app/main.py)
    │
    ├─► 2. Loads call context & history (SQLite)
    │
    ├─► 3. Sends prompt + tools to Groq / OpenAI (app/llm_agent.py)
    │       ├── Call `check_availability` (app/booking.py)
    │       ├── Call `book_appointment` (app/booking.py)
    │       └── Call `get_business_info` (business_info.json)
    │
    ├─► 4. Converts LLM response to MP3 audio via edge-tts (app/tts.py)
    │
    ├─► 5. Sends WhatsApp confirmation if appointment booked (app/whatsapp.py)
    │
    ▼ (TwiML <Play> Audio + <Gather> Speech)
 Twilio Voice Response (Spoken back to Caller)
```

---

## 🛠️ Prerequisites & Stack

| Component | Technology / Service | Tier / Cost |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.10+ & FastAPI | Open Source / Free |
| **Speech-to-Text (STT)** | Twilio Voice Speech Recognition | Free Trial Credit (~$15) |
| **Text-to-Speech (TTS)** | Microsoft `edge-tts` (`en-IN-NeerjaNeural`) | 100% Free / No API Key |
| **LLM Provider** | Groq API (`llama-3.3-70b-versatile`) or OpenAI | Free Tier (No Credit Card) |
| **WhatsApp Messages** | Twilio WhatsApp Sandbox | Included in Trial |
| **Database** | SQLite3 (`appointments.db`) | Embedded / Free |
| **Tunneling** | ngrok | Free Tier |

---

## 🚀 Quick Start Guide

### 1. Clone & Setup Environment

```bash
# Clone the repository
git clone https://github.com/<your-username>/voice-receptionist.git
cd voice-receptionist

# Create and activate Python virtual environment
python -m venv venv

# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```ini
# Twilio Console (https://console.twilio.com)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# LLM Provider (groq or openai)
LLM_PROVIDER=groq
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Public server URL (Updated after starting ngrok)
BASE_URL=https://your-ngrok-subdomain.ngrok-free.app

BUSINESS_INFO_PATH=business_info.json
DB_PATH=appointments.db
```

---

### 3. Test the AI Brain locally (Terminal Mode)

You can verify the agent logic, tool calling, and database bookings without setting up Twilio or ngrok:

```bash
python test_chat.py
```

*Example interaction:*
```text
Agent: Hi, thanks for calling! How can I help you today — booking an appointment, or a question?
You: Hi, I'd like to book a dental checkup tomorrow at 10 AM.
Agent: Can I have your name and phone number to complete the booking?
You: Alex, +919876543210
Agent: You're all set! I've booked a dental checkup for Alex on 2026-08-23 at 10:00.
[SYSTEM] Booking confirmed! {'success': True, ...}
```

---

### 4. Run the Voice Receptionist Server

#### Step A: Launch FastAPI Server
```bash
uvicorn app.main:app --reload --port 8000
```

#### Step B: Launch ngrok Tunnel
In a new terminal window:
```bash
ngrok http 8000
```
Copy the generated `https://xxxx.ngrok-free.app` URL, set it as `BASE_URL` in `.env`, and restart the FastAPI server.

---

### 5. Connect Twilio Phone Number

1. Go to **Twilio Console** → **Phone Numbers** → **Manage** → **Active Numbers**.
2. Click your active Twilio phone number.
3. Under **Voice & Fax** → **A call comes in**:
   - **URL**: `https://xxxx.ngrok-free.app/voice`
   - **HTTP Method**: `POST`
4. Click **Save**.

---

### 6. WhatsApp Sandbox Setup (Optional)

To receive WhatsApp confirmation messages on your phone:
1. In Twilio Console, go to **Messaging** → **Try it out** → **Send a WhatsApp message**.
2. Send the displayed join phrase (e.g., `join happy-tiger`) from your phone's WhatsApp to the sandbox number.

---

## 🔗 API Endpoints Summary

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/voice` | `POST` | Primary webhook hit by Twilio when a call connects. |
| `/gather` | `POST` | Webhook triggered when Twilio finishes transcribing caller speech. |
| `/voice-timeout` | `POST` | Fallback route when no caller speech is detected. |
| `/appointments` | `GET` | View all booked appointments in JSON format. |
| `/` | `GET` | Server health check. |

---

## ⚙️ Customizing Business Info & Booking Rules

- Edit [`business_info.json`](file:///c:/Users/SASHANK/Downloads/voice-receptionist/business_info.json) to update business name, hours, services, prices, and FAQs.
- Adjust slot intervals (`SLOT_MINUTES`), opening hours (`BUSINESS_OPEN_HOUR`), and closing hours (`BUSINESS_CLOSE_HOUR`) in [.env](file:///c:/Users/SASHANK/Downloads/voice-receptionist/.env).

---

## 📁 Repository Structure

```
voice-receptionist/
├── app/
│   ├── main.py          # FastAPI app & Twilio TwiML webhook handlers
│   ├── llm_agent.py      # LLM agent, system prompts, tool execution
│   ├── booking.py       # Availability checking & SQLite slot booking logic
│   ├── tts.py           # Microsoft edge-tts audio generator
│   ├── whatsapp.py      # WhatsApp confirmation messaging via Twilio
│   ├── database.py       # SQLite connection manager & table creation
│   └── config.py        # Centralized settings & environment loader
├── static/audio/        # Generated TTS MP3 speech files
├── business_info.json   # Business configuration (hours, services, FAQs)
├── test_chat.py         # Terminal interface for local testing
├── requirements.txt     # Python project dependencies
├── .env.example         # Template for environment variables
├── .gitignore           # Git exclusion rules
└── README.md            # Documentation
```

---

## 📜 License

This project is open-source and available under the [MIT License](LICENSE).
