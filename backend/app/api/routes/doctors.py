import uuid
from datetime import date as date_type, datetime, time, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.doctor import AvailabilityResponse, DoctorCreate, DoctorRead, DoctorUpdate

router = APIRouter(prefix="/doctors", tags=["doctors"])

SLOT_INTERVAL_MINUTES = 20


@router.post(
    "", response_model=DoctorRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.doctor, UserRole.admin))],
)
def create_doctor(
    payload: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.doctor and payload.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Doctors can only create their own profile")

    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if db.query(Doctor).filter(Doctor.user_id == payload.user_id).first():
        raise HTTPException(status_code=409, detail="Doctor profile already exists for this user")

    doctor = Doctor(**payload.model_dump())
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@router.get("", response_model=list[DoctorRead])
def list_doctors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Doctor).all()

@router.get("/me", response_model=DoctorRead)
def get_my_doctor_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="No doctor profile for this user")
    return doctor

@router.get("/{doctor_id}", response_model=DoctorRead)
def get_doctor(
    doctor_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return doctor


@router.patch("/{doctor_id}", response_model=DoctorRead)
def update_doctor(
    doctor_id: uuid.UUID,
    payload: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    if current_user.role != UserRole.admin and doctor.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this doctor")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(doctor, field, value)

    db.commit()
    db.refresh(doctor)
    return doctor


@router.get("/{doctor_id}/availability", response_model=AvailabilityResponse)
def get_doctor_availability(
    doctor_id: uuid.UUID,
    date: date_type = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    day_start = datetime.combine(date, time.min, tzinfo=timezone.utc)
    day_end = datetime.combine(date, time.max, tzinfo=timezone.utc)

    booked_times = {
        appt.scheduled_time
        for appt in db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.scheduled_time >= day_start,
            Appointment.scheduled_time <= day_end,
        )
        .all()
    }

    slots = []
    current = datetime.combine(date, doctor.working_hours_start, tzinfo=timezone.utc)
    end = datetime.combine(date, doctor.working_hours_end, tzinfo=timezone.utc)
    step = timedelta(minutes=SLOT_INTERVAL_MINUTES)

    while current < end:
        if current not in booked_times:
            slots.append(current.strftime("%H:%M"))
        current += step

    return AvailabilityResponse(doctor_id=doctor_id, date=date.isoformat(), available_slots=slots)