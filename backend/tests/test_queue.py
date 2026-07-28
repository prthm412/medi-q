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


def _today_at(hour: int, minute: int = 0) -> str:
    # Check-in deliberately only accepts same-day appointments — see queue.py —
    # so every appointment booked in this file uses *today's* date, not a
    # fixed future date like test_appointments.py uses.
    today = datetime.now(timezone.utc).date()
    return datetime.combine(today, time(hour, minute), tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def _book(client, doctor_id, patient_id, headers, room_id, hour, minute=0):
    payload = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "room_id": room_id,
        "scheduled_time": _today_at(hour, minute),
        "urgency_level": 2,
    }
    response = client.post("/appointments", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def test_checkin_creates_queue_position(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor, _, _ = _create_doctor(client, db_session, suffix)
    patient, _, patient_headers = _create_patient(client, db_session, suffix)
    appointment = _book(client, doctor["id"], patient["id"], patient_headers, room_id=1, hour=9)

    response = client.post("/queue/checkin", json={"appointment_id": appointment["id"]}, headers=patient_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["position"] == 1
    assert body["estimated_wait_minutes"] == 15


def test_checkin_twice_rejected(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor, _, _ = _create_doctor(client, db_session, suffix)
    patient, _, patient_headers = _create_patient(client, db_session, suffix)
    appointment = _book(client, doctor["id"], patient["id"], patient_headers, room_id=1, hour=9)

    first = client.post("/queue/checkin", json={"appointment_id": appointment["id"]}, headers=patient_headers)
    assert first.status_code == 201

    second = client.post("/queue/checkin", json={"appointment_id": appointment["id"]}, headers=patient_headers)
    assert second.status_code == 409


def test_checkin_rejects_other_patients_appointment(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor, _, _ = _create_doctor(client, db_session, suffix)
    patient_a, _, headers_a = _create_patient(client, db_session, suffix + "a")
    patient_b, _, headers_b = _create_patient(client, db_session, suffix + "b")
    appointment = _book(client, doctor["id"], patient_a["id"], headers_a, room_id=1, hour=9)

    response = client.post("/queue/checkin", json={"appointment_id": appointment["id"]}, headers=headers_b)
    assert response.status_code == 404


def test_position_reflects_check_in_order(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor, _, _ = _create_doctor(client, db_session, suffix)
    patient_a, _, headers_a = _create_patient(client, db_session, suffix + "a")
    patient_b, _, headers_b = _create_patient(client, db_session, suffix + "b")
    appt_a = _book(client, doctor["id"], patient_a["id"], headers_a, room_id=1, hour=9)
    appt_b = _book(client, doctor["id"], patient_b["id"], headers_b, room_id=2, hour=9, minute=20)

    first = client.post("/queue/checkin", json={"appointment_id": appt_a["id"]}, headers=headers_a)
    second = client.post("/queue/checkin", json={"appointment_id": appt_b["id"]}, headers=headers_b)
    assert first.json()["position"] == 1
    assert second.json()["position"] == 2


def test_completion_shifts_remaining_patient_via_websocket(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor, _, doctor_headers = _create_doctor(client, db_session, suffix)
    patient_a, _, headers_a = _create_patient(client, db_session, suffix + "a")
    patient_b, token_b, headers_b = _create_patient(client, db_session, suffix + "b")

    appt_a = _book(client, doctor["id"], patient_a["id"], headers_a, room_id=1, hour=9)
    appt_b = _book(client, doctor["id"], patient_b["id"], headers_b, room_id=2, hour=9, minute=20)

    client.post("/queue/checkin", json={"appointment_id": appt_a["id"]}, headers=headers_a)
    second_checkin = client.post("/queue/checkin", json={"appointment_id": appt_b["id"]}, headers=headers_b)
    assert second_checkin.json()["position"] == 2

    with client.websocket_connect(f"/ws/queue/{doctor['id']}?token={token_b}") as websocket:
        initial = websocket.receive_json()
        assert initial["patient_id"] == patient_b["id"]
        assert initial["position"] == 2

        complete = client.patch(
            f"/appointments/{appt_a['id']}/status",
            json={"status": "completed"},
            headers=doctor_headers,
        )
        assert complete.status_code == 200

        update = websocket.receive_json()
        assert update["type"] == "position_update"
        assert update["patient_id"] == patient_b["id"]
        assert update["position"] == 1
        assert update["estimated_wait_minutes"] == 15