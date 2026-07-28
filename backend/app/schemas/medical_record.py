import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

class MedicalRecordCreate(BaseModel):
    appointment_id: uuid.UUID
    notes: str

class MedicalRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    appointment_id: uuid.UUID
    notes: str
    created_at: datetime