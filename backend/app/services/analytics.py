from collections import defaultdict
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.enums import AppointmentStatus

CLINIC_TZ = ZoneInfo(settings.CLINIC_TIMEZONE)


def get_summary(db: Session, num_days: int) -> dict:
    today = datetime.now(CLINIC_TZ).date()
    first_day = today - timedelta(days=num_days - 1)
    range_start = datetime.combine(first_day, time.min, tzinfo=CLINIC_TZ).astimezone(timezone.utc)
    range_end = datetime.combine(today + timedelta(days=1), time.min, tzinfo=CLINIC_TZ).astimezone(timezone.utc)

    # Daily capacity = the sum of every doctor's max_daily_patients
    capacity = int(db.query(func.coalesce(func.sum(Doctor.max_daily_patients), 0)).scalar())

    appointments = (
        db.query(Appointment)
        .filter(Appointment.scheduled_time >= range_start, Appointment.scheduled_time < range_end)
        .all()
    )

    counts = defaultdict(lambda: {"booked": 0, "completed": 0, "no_show": 0})
    for a in appointments:
        day = a.scheduled_time.astimezone(CLINIC_TZ).date()
        counts[day]["booked"] += 1
        if a.status == AppointmentStatus.completed:
            counts[day]["completed"] += 1
        elif a.status == AppointmentStatus.no_show:
            counts[day]["no_show"] += 1

    days = []
    for i in range(num_days):
        day = first_day + timedelta(days=i)
        c = counts[day]
        days.append(
            {
                "date": day,
                "booked": c["booked"],
                "completed": c["completed"],
                "no_show": c["no_show"],
                "capacity": capacity,
                "occupancy_pct": round(100 * c["booked"] / capacity, 1) if capacity else 0.0,
            }
        )

    # No-show rate only counts appointments that have actually resolved
    resolved = sum(d["completed"] + d["no_show"] for d in days)
    no_shows = sum(d["no_show"] for d in days)

    return {
        "days": days,
        "no_show_rate_pct": round(100 * no_shows / resolved, 1) if resolved else 0.0,
    }