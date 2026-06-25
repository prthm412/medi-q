import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.enums import UserRole
from app.models.patient import Patient
from app.models.user import User
from app.schemas.appointment import AppointmentCreate, AppointmentRead, AppointmentStatusUpdate

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _assert_can_view_appointment(db: Session, current_user: User, appointment: Appointment):
    if current_user.role == UserRole.admin:
        return
    if current_user.role == UserRole.patient:
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if patient and patient.id == appointment.patient_id:
            return
    if current_user.role == UserRole.doctor:
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if doctor and doctor.id == appointment.doctor_id:
            return
    raise HTTPException(status_code=403, detail="Not authorized to view this appointment")


@router.post(
    "", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.patient, UserRole.admin))],
)
def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.patient:
        own_patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not own_patient or own_patient.id != payload.patient_id:
            raise HTTPException(status_code=403, detail="Patients can only book for themselves")

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


@router.get("", response_model=list[AppointmentRead], dependencies=[Depends(require_role(UserRole.admin))])
def list_appointments(db: Session = Depends(get_db)):
    return db.query(Appointment).all()


@router.get("/{appointment_id}", response_model=AppointmentRead)
def get_appointment(
    appointment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    _assert_can_view_appointment(db, current_user, appointment)
    return appointment


@router.patch(
    "/{appointment_id}/status", response_model=AppointmentRead,
    dependencies=[Depends(require_role(UserRole.doctor, UserRole.admin))],
)
def update_appointment_status(
    appointment_id: uuid.UUID,
    payload: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if current_user.role == UserRole.doctor:
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor or doctor.id != appointment.doctor_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this appointment")

    appointment.status = payload.status
    db.commit()
    db.refresh(appointment)
    return appointment