from datetime import date, time

from passlib.context import CryptContext

from app.db.session import SessionLocal
from app.models.doctor import Doctor
from app.models.enums import UserRole
from app.models.patient import Patient
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SEED_PASSWORD = "seed_password_123"  # synthetic dev accounts only, never real credentials

SEED_DOCTORS = [
    {"email": "dr.sharma@mediq.test", "name": "Dr. Anjali Sharma", "specialization": "General Medicine", "start": time(9, 0), "end": time(17, 0), "max_daily": 20},
    {"email": "dr.iyer@mediq.test", "name": "Dr. Karthik Iyer", "specialization": "Pediatrics", "start": time(10, 0), "end": time(18, 0), "max_daily": 15},
    {"email": "dr.khan@mediq.test", "name": "Dr. Ayesha Khan", "specialization": "Cardiology", "start": time(9, 0), "end": time(13, 0), "max_daily": 10},
]

SEED_PATIENTS = [
    {"email": "patient1@mediq.test", "name": "Asha Verma", "dob": date(1990, 4, 12), "contact_info": "9990000001"},
    {"email": "patient2@mediq.test", "name": "Rohan Gupta", "dob": date(1985, 11, 2), "contact_info": "9990000002"},
    {"email": "patient3@mediq.test", "name": "Meera Nair", "dob": date(2001, 7, 23), "contact_info": "9990000003"},
    {"email": "patient4@mediq.test", "name": "Vikram Singh", "dob": date(1978, 1, 30), "contact_info": "9990000004"},
    {"email": "patient5@mediq.test", "name": "Priya Das", "dob": date(1995, 9, 15), "contact_info": "9990000005"},
]


def get_or_create_user(db, email: str, role: UserRole) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(email=email, hashed_password=pwd_context.hash(SEED_PASSWORD), role=role)
    db.add(user)
    db.flush()
    return user


def seed() -> None:
    db = SessionLocal()
    try:
        for d in SEED_DOCTORS:
            user = get_or_create_user(db, d["email"], UserRole.doctor)
            if not db.query(Doctor).filter(Doctor.user_id == user.id).first():
                db.add(Doctor(
                    user_id=user.id,
                    name=d["name"],
                    specialization=d["specialization"],
                    working_hours_start=d["start"],
                    working_hours_end=d["end"],
                    max_daily_patients=d["max_daily"],
                ))

        for p in SEED_PATIENTS:
            user = get_or_create_user(db, p["email"], UserRole.patient)
            if not db.query(Patient).filter(Patient.user_id == user.id).first():
                db.add(Patient(
                    user_id=user.id,
                    name=p["name"],
                    dob=p["dob"],
                    contact_info=p["contact_info"],
                ))

        db.commit()
        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()