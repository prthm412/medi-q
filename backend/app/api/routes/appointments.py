import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.schemas.appointment import AppointmentCreate, AppointmentRead, AppointmentStatusUpdate

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    if not db.query(Patient).filter(Patient.id == payload.patient_id).first():
        raise HTTPException(status_code=404, detail="Patient not found")
    if not db.query(Doctor).filter(Doctor.id == payload.doctor_id).first():
        raise HTTPException(status_code=404, detail="Doctor not found")

    appointment = Appointment(**payload.model_dump())
    db.add(appointment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="This doctor or room is already booked for the requested time slot",
        )
    db.refresh(appointment)
    return appointment


@router.get("", response_model=list[AppointmentRead])
def list_appointments(db: Session = Depends(get_db)):
    return db.query(Appointment).all()


@router.get("/{appointment_id}", response_model=AppointmentRead)
def get_appointment(appointment_id: uuid.UUID, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.patch("/{appointment_id}/status", response_model=AppointmentRead)
def update_appointment_status(
    appointment_id: uuid.UUID, payload: AppointmentStatusUpdate, db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = payload.status
    db.commit()
    db.refresh(appointment)
    return appointment