"""
llm_agent.py
This is the "brain" of the receptionist. It keeps a conversation history
per call, sends it to an LLM with function-calling enabled, and executes
whichever tool the LLM decides to call (check availability, book, answer
an FAQ). This is the piece that makes the system an "agent" rather than a
scripted IVR menu — it decides what to do, not a rigid if/else tree.
"""
import json
from openai import OpenAI
from app.config import (
    OPENAI_API_KEY, GROQ_API_KEY, GROQ_BASE_URL,
    LLM_PROVIDER, LLM_MODEL, BUSINESS_INFO_PATH
)
from app.booking import get_available_slots, book_appointment

# Groq's API is OpenAI-compatible — same SDK, just a different base_url
# and API key. This is the only place the provider choice matters; every
# other line of agent logic below is identical either way.
if LLM_PROVIDER == "groq":
    client = OpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)
else:
    client = OpenAI(api_key=OPENAI_API_KEY)

with open(BUSINESS_INFO_PATH, "r") as f:
    BUSINESS_INFO = json.load(f)

SYSTEM_PROMPT = f"""
You are a warm, efficient AI phone receptionist for {BUSINESS_INFO['business_name']}.
You are speaking on a live PHONE CALL, so:
- Keep every reply SHORT (1-2 sentences). No lists, no markdown, no headers — this gets read aloud.
- Sound natural and conversational, like a helpful human receptionist.
- Ask only ONE question at a time.
- To book an appointment you need: caller's name, phone number, which service, a date, and a time.
  Collect these naturally over the conversation, don't interrogate the caller with all fields at once.
- Always check availability with the check_availability tool before confirming a time.
- Only call book_appointment once you have ALL required details AND the slot is confirmed available.
- If asked about hours, pricing, services, or general questions, use get_business_info.
- If the caller wants to end the call, say a brief, warm goodbye.

Business info you can reference directly:
Hours: {BUSINESS_INFO['hours']}
Services: {', '.join(s['name'] + ' (' + s['price'] + ')' for s in BUSINESS_INFO['services'])}
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Check available appointment time slots for a given date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date in YYYY-MM-DD format."}
                },
                "required": ["date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book a confirmed appointment. Only call this after confirming the slot is available and you have all details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "phone": {"type": "string", "description": "Caller's phone number in E.164 format, e.g. +919876543210"},
                    "service": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "time": {"type": "string", "description": "HH:MM in 24-hour format"}
                },
                "required": ["name", "phone", "service", "date", "time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_business_info",
            "description": "Look up hours, address, services, pricing, or FAQs for the business.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What the caller wants to know."}
                },
                "required": ["query"]
            }
        }
    }
]


def _execute_tool(tool_name: str, args: dict) -> dict:
    """Runs the actual Python function behind a tool the LLM chose to call."""
    if tool_name == "check_availability":
        slots = get_available_slots(args["date"])
        return {"available_slots": slots[:6]}  # cap so it stays a short spoken answer

    if tool_name == "book_appointment":
        return book_appointment(
            name=args["name"],
            phone=args["phone"],
            service=args["service"],
            date_str=args["date"],
            time_str=args["time"],
        )

    if tool_name == "get_business_info":
        return BUSINESS_INFO

    return {"error": f"Unknown tool {tool_name}"}


def get_agent_reply(history: list[dict]) -> tuple[str, list[dict], bool]:
    """
    Takes the full conversation history (list of {role, content} dicts),
    calls the LLM (possibly executing tools along the way), and returns:
      - reply_text: what the agent should say next
      - updated_history: history with this turn appended (save this for next call)
      - booking_confirmed: True if a book_appointment tool call succeeded this turn
        (main.py uses this flag to trigger the WhatsApp confirmation)
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    booking_confirmed = False
    booking_result = None

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        tools=TOOLS,
    )
    msg = response.choices[0].message

    # Loop to handle (possibly multiple) tool calls before the final spoken reply
    while msg.tool_calls:
        messages.append(msg.model_dump(exclude_none=True))
        for tool_call in msg.tool_calls:
            args = json.loads(tool_call.function.arguments)
            result = _execute_tool(tool_call.function.name, args)

            if tool_call.function.name == "book_appointment" and result.get("success"):
                booking_confirmed = True
                booking_result = {**result, "phone": args.get("phone")}

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result),
            })

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=TOOLS,
        )
        msg = response.choices[0].message

    reply_text = msg.content or "Sorry, could you repeat that?"
    messages.append({"role": "assistant", "content": reply_text})

    # Strip the system prompt back out before returning — main.py only
    # persists the user/assistant/tool turns, not the system prompt each time.
    updated_history = messages[1:]

    return reply_text, updated_history, (booking_confirmed, booking_result)
