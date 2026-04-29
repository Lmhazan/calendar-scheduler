import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

COLOR_MAP = {
    "affiliatenetwork": "5",   # Banana (yellow)
    "nokt": "11",              # Tomato (red)
    "workout": "9",            # Blueberry (blue)
    "networking": "3",         # Grape (purple)
    "spermworms": "6",         # Tangerine (orange)
    "career": "8",             # Graphite
    "life": None,              # Default
}


def get_calendar_service():
    from google.auth.transport.requests import Request

    creds = Credentials(
        token=None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    # Force a token refresh so we have a valid access token
    creds.refresh(Request())
    return build("calendar", "v3", credentials=creds)


def get_events_for_range(start_date: str, end_date: str, timezone: str) -> list:
    """Fetch all calendar events between two dates."""
    service = get_calendar_service()
    tz = ZoneInfo(timezone)

    start_dt = datetime.fromisoformat(start_date).replace(tzinfo=tz)
    end_dt = datetime.fromisoformat(end_date).replace(tzinfo=tz)

    result = service.events().list(
        calendarId=os.getenv("DEFAULT_CALENDAR_ID", "primary"),
        timeMin=start_dt.isoformat(),
        timeMax=end_dt.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = []
    for e in result.get("items", []):
        start = e.get("start", {}).get("dateTime", e.get("start", {}).get("date", ""))
        end = e.get("end", {}).get("dateTime", e.get("end", {}).get("date", ""))
        events.append({
            "summary": e.get("summary", ""),
            "start": start,
            "end": end,
        })
    return events


def get_free_slots(start_date: str, end_date: str, timezone: str,
                   work_start_hour: int = 8, work_end_hour: int = 19) -> list:
    """Return free time slots within working hours for a date range."""
    service = get_calendar_service()
    tz = ZoneInfo(timezone)

    start_dt = datetime.fromisoformat(start_date).replace(tzinfo=tz)
    end_dt = datetime.fromisoformat(end_date).replace(tzinfo=tz)

    body = {
        "timeMin": start_dt.isoformat(),
        "timeMax": end_dt.isoformat(),
        "timeZone": timezone,
        "items": [{"id": os.getenv("DEFAULT_CALENDAR_ID", "primary")}],
    }

    freebusy = service.freebusy().query(body=body).execute()
    busy_periods = freebusy["calendars"][os.getenv("DEFAULT_CALENDAR_ID", "primary")]["busy"]

    free_slots = []
    current = start_dt

    while current < end_dt:
        day_start = current.replace(hour=work_start_hour, minute=0, second=0, microsecond=0)
        day_end = current.replace(hour=work_end_hour, minute=0, second=0, microsecond=0)

        # Skip weekends
        if current.weekday() < 5:
            day_busy = []
            for b in busy_periods:
                b_start = datetime.fromisoformat(b["start"]).astimezone(tz)
                b_end = datetime.fromisoformat(b["end"]).astimezone(tz)
                if b_start < day_end and b_end > day_start:
                    day_busy.append((
                        max(b_start, day_start),
                        min(b_end, day_end)
                    ))
            day_busy.sort()

            slot_start = day_start
            for b_start, b_end in day_busy:
                if slot_start < b_start:
                    duration = int((b_start - slot_start).total_seconds() / 60)
                    if duration >= 15:
                        free_slots.append({
                            "start": slot_start.isoformat(),
                            "end": b_start.isoformat(),
                            "duration_minutes": duration,
                            "date": current.strftime("%A %b %d"),
                        })
                slot_start = max(slot_start, b_end)

            if slot_start < day_end:
                duration = int((day_end - slot_start).total_seconds() / 60)
                if duration >= 15:
                    free_slots.append({
                        "start": slot_start.isoformat(),
                        "end": day_end.isoformat(),
                        "duration_minutes": duration,
                        "date": current.strftime("%A %b %d"),
                    })

        current += timedelta(days=1)

    return free_slots


def create_calendar_events(events: list, timezone: str) -> list:
    """Create a batch of events on Google Calendar."""
    service = get_calendar_service()
    created = []

    for event in events:
        category = event.get("category", "").lower().replace(" ", "")
        color_id = COLOR_MAP.get(category)

        body = {
            "summary": event["summary"],
            "start": {"dateTime": event["start"], "timeZone": timezone},
            "end": {"dateTime": event["end"], "timeZone": timezone},
            "description": f"Scheduled by AI Calendar Assistant\nCategory: {event.get('category', '')}",
        }
        if color_id:
            body["colorId"] = color_id

        result = service.events().insert(
            calendarId=os.getenv("DEFAULT_CALENDAR_ID", "primary"),
            body=body
        ).execute()

        created.append({
            "summary": result["summary"],
            "start": result["start"]["dateTime"],
            "end": result["end"]["dateTime"],
            "link": result.get("htmlLink", ""),
        })

    return created
