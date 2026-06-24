import uuid
from datetime import date, datetime, time, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.enums import AppointmentStatus, UserRole
from app.models.patient import Patient
from app.models.user import User


def _make_doctor(db, suffix):
    user = User(email=f"doc-{suffix}@test.local", hashed_password="x", role=UserRole.doctor)
    db.add(user)
    db.flush()
    doctor = Doctor(
        user_id=user.id, specialization="General Medicine",
        working_hours_start=time(9, 0), working_hours_end=time(17, 0),
        max_daily_patients=20,
    )
    db.add(doctor)
    db.flush()
    return doctor


def _make_patient(db, suffix):
    user = User(email=f"pat-{suffix}@test.local", hashed_password="x", role=UserRole.patient)
    db.add(user)
    db.flush()
    patient = Patient(user_id=user.id, name="Test Patient", dob=date(1990, 1, 1), contact_info="0000000000")
    db.add(patient)
    db.flush()
    return patient


def test_double_booking_same_doctor_same_slot_rejected(db):
    doctor = _make_doctor(db, uuid.uuid4().hex[:8])
    patient_a = _make_patient(db, uuid.uuid4().hex[:8])
    patient_b = _make_patient(db, uuid.uuid4().hex[:8])
    slot = datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc)

    db.add(Appointment(patient_id=patient_a.id, doctor_id=doctor.id, room_id=1,
                        scheduled_time=slot, status=AppointmentStatus.scheduled, urgency_level=3))
    db.flush()

    db.add(Appointment(patient_id=patient_b.id, doctor_id=doctor.id, room_id=2,
                        scheduled_time=slot, status=AppointmentStatus.scheduled, urgency_level=3))
    with pytest.raises(IntegrityError):
        db.flush()


def test_double_booking_same_room_same_slot_rejected(db):
    doctor_a = _make_doctor(db, uuid.uuid4().hex[:8])
    doctor_b = _make_doctor(db, uuid.uuid4().hex[:8])
    patient_a = _make_patient(db, uuid.uuid4().hex[:8])
    patient_b = _make_patient(db, uuid.uuid4().hex[:8])
    slot = datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc)

    db.add(Appointment(patient_id=patient_a.id, doctor_id=doctor_a.id, room_id=5,
                        scheduled_time=slot, status=AppointmentStatus.scheduled, urgency_level=2))
    db.flush()

    db.add(Appointment(patient_id=patient_b.id, doctor_id=doctor_b.id, room_id=5,
                        scheduled_time=slot, status=AppointmentStatus.scheduled, urgency_level=2))
    with pytest.raises(IntegrityError):
        db.flush()