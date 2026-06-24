import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

class PatientCreate(BaseModel):
    user_id: uuid.UUID
    name: str
    dob: date
    contact_info: str

class PatientUpdate(BaseModel):
    name: str | None = None
    contact_info: str | None = None

class PatientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    dob: date
    contact_info: str