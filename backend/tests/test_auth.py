import uuid
from datetime import date

from app.core.security import create_access_token
from app.models.enums import UserRole
from app.models.patient import Patient
from app.models.user import User


def _signup(client, suffix: str, role: UserRole, password: str = "testpass123"):
    payload = {"email": f"{role.value}-{suffix}@example.com", "password": password, "role": role.value}
    response = client.post("/auth/signup", json=payload)
    assert response.status_code == 201
    return response.json()


def _login(client, email: str, password: str = "testpass123"):
    return client.post("/auth/login", json={"email": email, "password": password})


def _make_user_with_token(db_session, suffix: str, role: UserRole):
    user = User(email=f"{role.value}-{suffix}@test.local", hashed_password="x", role=role)
    db_session.add(user)
    db_session.flush()
    token = create_access_token(subject=str(user.id), role=role.value)
    return user, {"Authorization": f"Bearer {token}"}


# --- Signup / login happy paths, all three roles ---

def test_signup_and_login_patient(client):
    suffix = uuid.uuid4().hex[:8]
    user = _signup(client, suffix, UserRole.patient)
    assert user["role"] == "patient"
    assert "password" not in user and "hashed_password" not in user

    login = _login(client, user["email"])
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert "access_token" in login.json()


def test_signup_and_login_doctor(client):
    suffix = uuid.uuid4().hex[:8]
    user = _signup(client, suffix, UserRole.doctor)
    assert user["role"] == "doctor"
    assert _login(client, user["email"]).status_code == 200


def test_signup_and_login_admin(client):
    suffix = uuid.uuid4().hex[:8]
    user = _signup(client, suffix, UserRole.admin)
    assert user["role"] == "admin"
    assert _login(client, user["email"]).status_code == 200


def test_signup_duplicate_email_rejected(client):
    suffix = uuid.uuid4().hex[:8]
    user = _signup(client, suffix, UserRole.patient)

    response = client.post("/auth/signup", json={
        "email": user["email"], "password": "another_pass", "role": "patient",
    })
    assert response.status_code == 409


def test_login_wrong_password_rejected(client):
    suffix = uuid.uuid4().hex[:8]
    user = _signup(client, suffix, UserRole.patient)
    assert _login(client, user["email"], password="wrong_password").status_code == 401


def test_login_nonexistent_email_rejected(client):
    assert _login(client, "nobody@example.com", password="whatever").status_code == 401


# --- Explicit cross-role denial cases ---

def test_unauthenticated_request_rejected(client):
    response = client.get("/patients")
    assert response.status_code in (401, 403)


def test_patient_cannot_list_all_patients(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    _, headers = _make_user_with_token(db_session, suffix, UserRole.patient)
    response = client.get("/patients", headers=headers)
    assert response.status_code == 403


def test_patient_cannot_view_another_patients_profile(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    patient_a, headers_a = _make_user_with_token(db_session, suffix + "a", UserRole.patient)
    patient_b, _ = _make_user_with_token(db_session, suffix + "b", UserRole.patient)

    profile_a = Patient(user_id=patient_a.id, name="A", dob=date(1990, 1, 1), contact_info="111")
    profile_b = Patient(user_id=patient_b.id, name="B", dob=date(1991, 1, 1), contact_info="222")
    db_session.add_all([profile_a, profile_b])
    db_session.flush()

    response = client.get(f"/patients/{profile_b.id}", headers=headers_a)
    assert response.status_code == 403


def test_unassigned_doctor_cannot_view_patient(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    _, doctor_headers = _make_user_with_token(db_session, suffix, UserRole.doctor)
    patient_user, _ = _make_user_with_token(db_session, suffix + "p", UserRole.patient)

    profile = Patient(user_id=patient_user.id, name="Unrelated", dob=date(1992, 2, 2), contact_info="333")
    db_session.add(profile)
    db_session.flush()

    response = client.get(f"/patients/{profile.id}", headers=doctor_headers)
    assert response.status_code == 403


def test_doctor_cannot_create_appointment(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    _, doctor_headers = _make_user_with_token(db_session, suffix, UserRole.doctor)

    response = client.post("/appointments", json={
        "patient_id": str(uuid.uuid4()),
        "doctor_id": str(uuid.uuid4()),
        "room_id": 1,
        "scheduled_time": "2026-07-04T09:00:00Z",
        "urgency_level": 2,
    }, headers=doctor_headers)
    assert response.status_code == 403


def test_patient_cannot_complete_appointment(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    _, patient_headers = _make_user_with_token(db_session, suffix, UserRole.patient)

    response = client.patch(
        f"/appointments/{uuid.uuid4()}/status",
        json={"status": "completed"},
        headers=patient_headers,
    )
    assert response.status_code == 403