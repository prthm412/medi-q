import uuid

from pydantic import BaseModel


class CheckInRequest(BaseModel):
    appointment_id: uuid.UUID


class QueuePositionResponse(BaseModel):
    patient_id: uuid.UUID
    position: int
    estimated_wait_minutes: int