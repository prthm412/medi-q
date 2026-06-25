import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.enums import UserRole
from app.models.patient import Patient
from app.models.user import User
from app.schemas.appointment import AppointmentRead
from app.schemas.patient import PatientCreate, PatientRead, PatientUpdate

router = APIRouter(prefix="/patients", tags=["patients"])


def _is_assigned_doctor(db: Session, doctor_user: User, patient_id: uuid.UUID) -> bool:
    doctor = db.query(Doctor).filter(Doctor.user_id == doctor_user.id).first()
    if not doctor:
        return False
    return (
        db.query(Appointment)
        .filter(Appointment.doctor_id == doctor.id, Appointment.patient_id == patient_id)
        .first()
        is not None
    )


def _assert_can_view_patient(db: Session, current_user: User, patient: Patient):
    if current_user.role == UserRole.admin:
        return
    if current_user.role == UserRole.patient and patient.user_id == current_user.id:
        return
    if current_user.role == UserRole.doctor and _is_assigned_doctor(db, current_user, patient.id):
        return
    raise HTTPException(status_code=403, detail="Not authorized to view this patient")


@router.post(
    "", response_model=PatientRead, status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.patient, UserRole.admin))],
)
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.patient and payload.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Patients can only create their own profile")

    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if db.query(Patient).filter(Patient.user_id == payload.user_id).first():
        raise HTTPException(status_code=409, detail="Patient profile already exists for this user")

    patient = Patient(**payload.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@router.get("", response_model=list[PatientRead], dependencies=[Depends(require_role(UserRole.admin))])
def list_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()


@router.get("/{patient_id}", response_model=PatientRead)
def get_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    _assert_can_view_patient(db, current_user, patient)
    return patient


@router.patch("/{patient_id}", response_model=PatientRead)
def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    if current_user.role != UserRole.admin and patient.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this patient")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(patient, field, value)

    db.commit()
    db.refresh(patient)
    return patient


@router.get("/{patient_id}/appointments", response_model=list[AppointmentRead])
def get_patient_appointments(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    _assert_can_view_patient(db, current_user, patient)
    return db.query(Appointment).filter(Appointment.patient_id == patient_id).all()