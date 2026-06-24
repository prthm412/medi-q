import uuid

from app.models.enums import UserRole
from app.models.user import User


def _make_user(db_session, suffix: str, role: UserRole) -> User:
    user = User(email=f"{role.value}-{suffix}@test.local", hashed_password="x", role=role)
    db_session.add(user)
    db_session.flush()
    return user


def _create_doctor(client, db_session, suffix: str) -> dict:
    user = _make_user(db_session, suffix, UserRole.doctor)
    payload = {
        "user_id": str(user.id),
        "specialization": "General Medicine",
        "working_hours_start": "09:00:00",
        "working_hours_end": "17:00:00",
        "max_daily_patients": 20,
    }
    response = client.post("/doctors", json=payload)
    assert response.status_code == 201
    return response.json()


def _create_patient(client, db_session, suffix: str) -> dict:
    user = _make_user(db_session, suffix, UserRole.patient)
    payload = {
        "user_id": str(user.id),
        "name": "Test Patient",
        "dob": "1990-01-01",
        "contact_info": "0000000000",
    }
    response = client.post("/patients", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_appointment_succeeds(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor = _create_doctor(client, db_session, suffix)
    patient = _create_patient(client, db_session, suffix)

    payload = {
        "patient_id": patient["id"],
        "doctor_id": doctor["id"],
        "room_id": 1,
        "scheduled_time": "2026-07-01T09:00:00Z",
        "urgency_level": 3,
    }
    response = client.post("/appointments", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "scheduled"
    assert body["doctor_id"] == doctor["id"]


def test_double_booking_same_doctor_rejected(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor = _create_doctor(client, db_session, suffix)
    patient_a = _create_patient(client, db_session, suffix + "a")
    patient_b = _create_patient(client, db_session, suffix + "b")

    slot = "2026-07-02T10:00:00Z"

    first = client.post("/appointments", json={
        "patient_id": patient_a["id"],
        "doctor_id": doctor["id"],
        "room_id": 2,
        "scheduled_time": slot,
        "urgency_level": 2,
    })
    assert first.status_code == 201

    second = client.post("/appointments", json={
        "patient_id": patient_b["id"],
        "doctor_id": doctor["id"],
        "room_id": 3,
        "scheduled_time": slot,
        "urgency_level": 4,
    })
    assert second.status_code == 409


def test_availability_excludes_booked_slot(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor = _create_doctor(client, db_session, suffix)
    patient = _create_patient(client, db_session, suffix)

    booked_time = "2026-07-03T09:00:00Z"
    response = client.post("/appointments", json={
        "patient_id": patient["id"],
        "doctor_id": doctor["id"],
        "room_id": 4,
        "scheduled_time": booked_time,
        "urgency_level": 1,
    })
    assert response.status_code == 201

    availability = client.get(f"/doctors/{doctor['id']}/availability", params={"date": "2026-07-03"})
    assert availability.status_code == 200
    slots = availability.json()["available_slots"]
    assert "09:00" not in slots
    assert "09:20" in slots