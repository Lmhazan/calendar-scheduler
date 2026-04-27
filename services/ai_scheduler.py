import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an AI calendar scheduling assistant for Lucas Hazan.

Your job is to:
1. Parse a list of to-dos
2. Categorize each task
3. Estimate realistic durations
4. Schedule them into available free time slots intelligently

CATEGORIES & COLORS (always use these exact category names):
- affiliatenetwork → yellow (affiliate network work)
- nokt → red (Nokt business)
- spermworms → orange (Spermworms business)
- workout → blue (exercise/fitness)
- networking → purple (connecting with people, coffee chats)
- career → graphite (job related)
- life → default (personal errands, finances, etc.)

SCHEDULING RULES:
- Place high-priority tasks earlier in the day
- Group similar categories together when possible
- Leave buffer time between tasks (don't pack the schedule)
- Respect fixed/anchored times if the user specifies them (e.g. "at 2pm", "@ 3pm")
- Don't schedule past 7pm unless necessary
- Typical durations: quick task=15-30min, medium=45-60min, deep work=90-120min
- "Flow state" or deep work blocks should be 90+ minutes

Return ONLY a valid JSON array of scheduled events, no explanation text.

Each event object must have:
{
  "summary": "event title",
  "category": "category name from list above",
  "start": "ISO 8601 datetime with timezone offset",
  "end": "ISO 8601 datetime with timezone offset",
  "priority": "high|medium|low",
  "notes": "optional brief note"
}"""


def parse_and_schedule(
    todos_text: str,
    existing_events: list,
    free_slots: list,
    start_date: str,
    timezone: str,
) -> dict:
    """Use Claude to parse todos and generate a schedule."""

    user_message = f"""Please schedule these to-dos into my calendar.

START DATE: {start_date}
TIMEZONE: {timezone}

TO-DOS:
{todos_text}

EXISTING CALENDAR EVENTS (already booked):
{json.dumps(existing_events, indent=2)}

FREE TIME SLOTS AVAILABLE:
{json.dumps(free_slots, indent=2)}

Instructions:
- Only schedule into the FREE TIME SLOTS provided
- Do not overlap with existing events
- Return a JSON array of scheduled events
- For tasks with a specified time (e.g. "at 2pm"), use that exact time
- Prioritize high-urgency tasks earlier in the week/day"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()

    # Strip markdown code blocks if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        events = json.loads(raw)
        return {"success": True, "events": events}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Failed to parse AI response: {str(e)}", "raw": raw}
