import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from services.gcal import get_events_for_range, get_free_slots, create_calendar_events
from services.ai_scheduler import parse_and_schedule

app = FastAPI(title="AI Calendar Scheduler")
templates = Jinja2Templates(directory="templates")


# ── Models ──────────────────────────────────────────────────────────────────

class ScheduleRequest(BaseModel):
    todos: str
    start_date: str        # YYYY-MM-DD
    end_date: str          # YYYY-MM-DD
    timezone: str = "America/New_York"


class ConfirmRequest(BaseModel):
    events: list
    timezone: str = "America/New_York"


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/schedule")
async def schedule_todos(req: ScheduleRequest):
    """Parse todos + fetch calendar data, return a proposed schedule."""
    try:
        # Extend end_date by 1 day for inclusive range
        tz = ZoneInfo(req.timezone)
        end_dt = datetime.fromisoformat(req.end_date)
        end_inclusive = (end_dt + timedelta(days=1)).strftime("%Y-%m-%dT23:59:59")

        existing = get_events_for_range(
            f"{req.start_date}T00:00:00",
            end_inclusive,
            req.timezone,
        )
        free_slots = get_free_slots(
            f"{req.start_date}T00:00:00",
            end_inclusive,
            req.timezone,
        )

        result = parse_and_schedule(
            todos_text=req.todos,
            existing_events=existing,
            free_slots=free_slots,
            start_date=req.start_date,
            timezone=req.timezone,
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "AI scheduling failed"))

        return JSONResponse({
            "events": result["events"],
            "free_slots": free_slots,
            "existing_count": len(existing),
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/confirm")
async def confirm_schedule(req: ConfirmRequest):
    """Create confirmed events on Google Calendar."""
    try:
        created = create_calendar_events(req.events, req.timezone)
        return JSONResponse({"created": created, "count": len(created)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}
