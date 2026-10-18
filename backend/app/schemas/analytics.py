from datetime import date as date_type

from pydantic import BaseModel

class DailyStats(BaseModel):
    date: date_type
    booked: int
    completed: int
    no_show: int
    capacity: int
    occupancy_pct: float

class AnalyticsSummary(BaseModel):
    days: list[DailyStats]
    no_show_rate_pct: float