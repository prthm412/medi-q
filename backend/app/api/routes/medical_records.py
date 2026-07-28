from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.enums import UserRole
from app.models.medical_record import MedicalRecord
from app.models.user import User
from app.schemas.medical_record import MedicalRecordCreate, MedicalRecordRead


router = APIRouter(prefix="/medical-records", tags=["medical-records"])

@router.post(
    "",
    response_model=MedicalRecordRead,
    status_code=201,
    dependencies=[Depends(require_role(UserRole.doctor, UserRole.admin))],
)
def create_medical_record(
    payload: MedicalRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = db.query(Appointment).filter(Appointment.id == payload.appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if current_user.role == UserRole.doctor:
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor or doctor.id != appointment.doctor_id:
            raise HTTPException(status_code=403, detail="Not authorized to record notes for this appointment")

    if db.query(MedicalRecord).filter(MedicalRecord.appointment_id == appointment.id).first():
        raise HTTPException(status_code=409, detail="A medical record already exists for this appointment")

    record = MedicalRecord(
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        appointment_id=appointment.id,
        notes=payload.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record