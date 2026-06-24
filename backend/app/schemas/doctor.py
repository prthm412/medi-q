import uuid
from datetime import time

from pydantic import BaseModel, ConfigDict, Field


class DoctorCreate(BaseModel):
    user_id: uuid.UUID
    specialization: str
    working_hours_start: time
    working_hours_end: time
    max_daily_patients: int = Field(gt=0)


class DoctorUpdate(BaseModel):
    specialization: str | None = None
    working_hours_start: time | None = None
    working_hours_end: time | None = None
    max_daily_patients: int | None = Field(default=None, gt=0)


class DoctorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    specialization: str
    working_hours_start: time
    working_hours_end: time
    max_daily_patients: int


class AvailabilityResponse(BaseModel):
    doctor_id: uuid.UUID
    date: str
    available_slots: list[str]