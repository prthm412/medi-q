import uuid
from datetime import datetime, time, timezone

from app.core.security import create_access_token
from app.models.enums import UserRole
from app.models.user import User


def _make_user(db_session, suffix: str, role: UserRole):
    user = User(email=f"{role.value}-{suffix}@test.local", hashed_password="x", role=role)
    db_session.add(user)
    db_session.flush()
    token = create_access_token(subject=str(user.id), role=role.value)
    return user, token, {"Authorization": f"Bearer {token}"}


def _create_doctor(client, db_session, suffix: str):
    user, token, headers = _make_user(db_session, suffix, UserRole.doctor)
    payload = {
        "user_id": str(user.id),
        "name": "Test Doctor",
        "specialization": "General Medicine",
        "working_hours_start": "09:00:00",
        "working_hours_end": "17:00:00",
        "max_daily_patients": 20,
    }
    response = client.post("/doctors", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json(), token, headers


def _create_patient(client, db_session, suffix: str):
    user, token, headers = _make_user(db_session, suffix, UserRole.patient)
    payload = {
        "user_id": str(user.id),
        "name": "Test Patient",
        "dob": "1990-01-01",
        "contact_info": "0000000000",
    }
    response = client.post("/patients", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json(), token, headers


def _book(client, doctor_id, patient_id, headers, room_id, hour=9):
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "room_id": room_id,
        "scheduled_time": f"2026-08-{room_id:02d}T{hour:02d}:00:00Z",
        "urgency_level": 2,
    }
    response = client.post("/appointments", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_doctor_creates_medical_record(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor, _, doctor_headers = _create_doctor(client, db_session, suffix)
    patient, _, patient_headers = _create_patient(client, db_session, suffix)
    appointment = _book(client, doctor["id"], patient["id"], patient_headers, room_id=1)

    response = client.post(
        "/medical-records",
        json={"appointment_id": appointment["id"], "notes": "Prescribed rest and fluids."},
        headers=doctor_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["appointment_id"] == appointment["id"]
    assert body["patient_id"] == patient["id"]
    assert body["doctor_id"] == doctor["id"]


def test_duplicate_medical_record_for_same_appointment_rejected(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor, _, doctor_headers = _create_doctor(client, db_session, suffix)
    patient, _, patient_headers = _create_patient(client, db_session, suffix)
    appointment = _book(client, doctor["id"], patient["id"], patient_headers, room_id=2)

    first = client.post(
        "/medical-records",
        json={"appointment_id": appointment["id"], "notes": "First visit notes."},
        headers=doctor_headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/medical-records",
        json={"appointment_id": appointment["id"], "notes": "Duplicate attempt."},
        headers=doctor_headers,
    )
    assert second.status_code == 409


def test_unassigned_doctor_cannot_create_medical_record(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor_a, _, headers_a = _create_doctor(client, db_session, suffix + "a")
    doctor_b, _, headers_b = _create_doctor(client, db_session, suffix + "b")
    patient, _, patient_headers = _create_patient(client, db_session, suffix)
    appointment = _book(client, doctor_a["id"], patient["id"], patient_headers, room_id=3)

    response = client.post(
        "/medical-records",
        json={"appointment_id": appointment["id"], "notes": "Should not be allowed."},
        headers=headers_b,
    )
    assert response.status_code == 403


def test_patient_cannot_create_medical_record(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor, _, doctor_headers = _create_doctor(client, db_session, suffix)
    patient, _, patient_headers = _create_patient(client, db_session, suffix)
    appointment = _book(client, doctor["id"], patient["id"], patient_headers, room_id=4)

    response = client.post(
        "/medical-records",
        json={"appointment_id": appointment["id"], "notes": "Patient trying to self-diagnose."},
        headers=patient_headers,
    )
    assert response.status_code == 403