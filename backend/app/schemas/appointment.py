import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AppointmentStatus


class AppointmentCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    room_id: int
    scheduled_time: datetime
    urgency_level: int = Field(ge=1, le=5)


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus


class AppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    room_id: int
    scheduled_time: datetime
    status: AppointmentStatus
    urgency_level: int
    created_at: datetime