"""
booking.py
All appointment-scheduling logic lives here: generating valid slots for a
day, checking whether a slot is free, and saving a confirmed booking.
This is the "tool" the LLM agent calls when it decides to check availability
or book an appointment — see llm_agent.py.
"""
from datetime import datetime, timedelta
from app.database import get_conn
from app.config import BUSINESS_OPEN_HOUR, BUSINESS_CLOSE_HOUR, SLOT_MINUTES


def _all_slots_for_day() -> list[str]:
    """Generate every possible HH:MM slot for a business day, e.g. ['09:00','09:30',...]."""
    slots = []
    start = datetime.strptime(f"{BUSINESS_OPEN_HOUR}:00", "%H:%M")
    end = datetime.strptime(f"{BUSINESS_CLOSE_HOUR}:00", "%H:%M")
    cur = start
    while cur < end:
        slots.append(cur.strftime("%H:%M"))
        cur += timedelta(minutes=SLOT_MINUTES)
    return slots


def get_available_slots(date_str: str) -> list[str]:
    """
    Returns free HH:MM slots for a given YYYY-MM-DD date.
    date_str must already be normalized to YYYY-MM-DD by the LLM/tool layer.
    """
    all_slots = _all_slots_for_day()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT appt_time FROM appointments WHERE appt_date = ?", (date_str,)
        ).fetchall()
    taken = {r["appt_time"] for r in rows}
    return [s for s in all_slots if s not in taken]


def is_slot_available(date_str: str, time_str: str) -> bool:
    return time_str in get_available_slots(date_str)


def book_appointment(name: str, phone: str, service: str, date_str: str, time_str: str) -> dict:
    """
    Books the appointment if the slot is free. Returns a result dict —
    never raises, so the LLM agent can turn the result straight into speech.
    """
    if not is_slot_available(date_str, time_str):
        return {
            "success": False,
            "message": f"Sorry, {time_str} on {date_str} is no longer available."
        }

    with get_conn() as conn:
        conn.execute(
            """INSERT INTO appointments (caller_name, caller_phone, service, appt_date, appt_time)
               VALUES (?, ?, ?, ?, ?)""",
            (name, phone, service, date_str, time_str)
        )
        conn.commit()

    return {
        "success": True,
        "message": f"Booked {service} for {name} on {date_str} at {time_str}."
    }
