from datetime import date as date_type, datetime, time, timedelta, timezone

import scheduler_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.enums import AppointmentStatus


def _time_to_min(t: time) -> int:
    return t.hour * 60 + t.minute


def _min_to_datetime(day: date_type, minutes: int) -> datetime:
    return datetime.combine(day, time.min, tzinfo=timezone.utc) + timedelta(minutes=minutes)


def optimize_day(db: Session, target_date: date_type) -> dict:
    day_start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.status == AppointmentStatus.scheduled,
            Appointment.scheduled_time >= day_start,
            Appointment.scheduled_time < day_end,
        )
        .all()
    )
    doctors = db.query(Doctor).all()
    doctor_by_id = {d.id: d for d in doctors}

    # The C++ optimizer works with plain ints; map list-index <-> real UUIDs
    # so results can be written back to the right rows.
    doctor_index_to_uuid = {i: d.id for i, d in enumerate(doctors)}
    appt_index_to_appointment = {i: a for i, a in enumerate(appointments)}

    now = datetime.now(timezone.utc)

    cpp_doctors = [
        scheduler_engine.Doctor(
            i,
            d.specialization,
            _time_to_min(d.working_hours_start),
            _time_to_min(d.working_hours_end),
            d.max_daily_patients,
        )
        for i, d in enumerate(doctors)
    ]

    cpp_patients = [
        scheduler_engine.Patient(
            i,
            a.urgency_level,
            # minutes since booked, as a fairness tiebreaker (no live check-in
            # wait exists yet at optimize-time, unlike the Phase 5 queue)
            max(0, int((now - a.created_at.replace(tzinfo=timezone.utc)).total_seconds() // 60)),
            # required specialization = whichever doctor they're currently
            # booked with, so re-optimization can't move them to a doctor
            # who isn't qualified to see them
            doctor_by_id[a.doctor_id].specialization,
        )
        for i, a in enumerate(appointments)
    ]

    result = scheduler_engine.optimize(cpp_patients, cpp_doctors)

    assignments_out = []
    for assignment in result.assignments:
        appointment = appt_index_to_appointment[assignment.patient_id]
        new_doctor = doctor_by_id[doctor_index_to_uuid[assignment.doctor_id]]
        new_time = _min_to_datetime(target_date, assignment.scheduled_time_min)

        # Per-row savepoint: a room/doctor-slot conflict on one reassignment
        # (the optimizer never touches room_id, only doctor_id/time) should
        # skip that row, not roll back every other valid assignment in the batch.
        savepoint = db.begin_nested()
        appointment.doctor_id = new_doctor.id
        appointment.scheduled_time = new_time
        try:
            db.flush()
            savepoint.commit()
        except IntegrityError:
            savepoint.rollback()
            continue

        assignments_out.append(
            {
                "patient_id": str(appointment.patient_id),
                "doctor_id": str(new_doctor.id),
                "room_id": appointment.room_id,
                "scheduled_time": new_time.isoformat(),
            }
        )

    db.commit()

    unassigned = [
        str(appt_index_to_appointment[pid].patient_id) for pid in result.unassigned_patient_ids
    ]

    return {
        "date": target_date,
        "assignments": assignments_out,
        "unassigned_patient_ids": unassigned,
        "objective_value": result.objective_value,
    }