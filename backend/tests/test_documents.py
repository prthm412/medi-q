import uuid

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
        "scheduled_time": f"2026-09-{room_id:02d}T{hour:02d}:00:00Z",
        "urgency_level": 2,
    }
    response = client.post("/appointments", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


def _add_medical_record(client, appointment_id, doctor_headers, notes="Prescribed rest."):
    response = client.post(
        "/medical-records",
        json={"appointment_id": appointment_id, "notes": notes},
        headers=doctor_headers,
    )
    assert response.status_code == 201
    return response.json()


def test_prescription_pdf_returned_for_valid_appointment(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor, _, doctor_headers = _create_doctor(client, db_session, suffix)
    patient, _, patient_headers = _create_patient(client, db_session, suffix)
    appointment = _book(client, doctor["id"], patient["id"], patient_headers, room_id=1)
    _add_medical_record(client, appointment["id"], doctor_headers, notes="Amoxicillin 500mg, 3x daily.")

    response = client.get(f"/documents/{appointment['id']}/prescription", headers=doctor_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"
    assert len(response.content) > 500


def test_prescription_404_when_no_medical_record_exists(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor, _, doctor_headers = _create_doctor(client, db_session, suffix)
    patient, _, patient_headers = _create_patient(client, db_session, suffix)
    appointment = _book(client, doctor["id"], patient["id"], patient_headers, room_id=2)

    response = client.get(f"/documents/{appointment['id']}/prescription", headers=doctor_headers)
    assert response.status_code == 404


def test_other_patient_cannot_fetch_prescription(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor, _, doctor_headers = _create_doctor(client, db_session, suffix)
    patient_a, _, headers_a = _create_patient(client, db_session, suffix + "a")
    patient_b, _, headers_b = _create_patient(client, db_session, suffix + "b")
    appointment = _book(client, doctor["id"], patient_a["id"], headers_a, room_id=3)
    _add_medical_record(client, appointment["id"], doctor_headers)

    response = client.get(f"/documents/{appointment['id']}/prescription", headers=headers_b)
    assert response.status_code == 403


def test_unassigned_doctor_cannot_fetch_prescription(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor_a, _, headers_a = _create_doctor(client, db_session, suffix + "a")
    doctor_b, _, headers_b = _create_doctor(client, db_session, suffix + "b")
    patient, _, patient_headers = _create_patient(client, db_session, suffix)
    appointment = _book(client, doctor_a["id"], patient["id"], patient_headers, room_id=4)
    _add_medical_record(client, appointment["id"], headers_a)

    response = client.get(f"/documents/{appointment['id']}/prescription", headers=headers_b)
    assert response.status_code == 403


def test_admin_can_fetch_any_prescription(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    doctor, _, doctor_headers = _create_doctor(client, db_session, suffix)
    patient, _, patient_headers = _create_patient(client, db_session, suffix)
    appointment = _book(client, doctor["id"], patient["id"], patient_headers, room_id=5)
    _add_medical_record(client, appointment["id"], doctor_headers)

    _, _, admin_headers = _make_user(db_session, suffix, UserRole.admin)
    response = client.get(f"/documents/{appointment['id']}/prescription", headers=admin_headers)
    assert response.status_code == 200