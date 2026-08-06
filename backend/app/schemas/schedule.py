from datetime import date as date_type

from pydantic import BaseModel


class ScheduleOptimizeRequest(BaseModel):
    date: date_type


class ScheduleAssignment(BaseModel):
    patient_id: str
    doctor_id: str
    room_id: int
    scheduled_time: str


class ScheduleOptimizeResponse(BaseModel):
    date: date_type
    assignments: list[ScheduleAssignment]
    unassigned_patient_ids: list[str]
    objective_value: float