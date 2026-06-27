"""
Mirrors the C++ Patient/Doctor/Assignment shapes so benchmark.py can swap
between the two implementations with the same input data and compare
results on equal footing.
"""

from dataclasses import dataclass, field

SLOT_DURATION_MIN = 20  # must match scheduler_engine/src/scheduler.h


@dataclass
class Patient:
    id: int
    urgency_level: int
    wait_minutes: int
    preferred_specialization: str = ""


@dataclass
class Doctor:
    id: int
    specialization: str
    working_start_min: int
    working_end_min: int
    max_daily_patients: int


@dataclass
class Assignment:
    patient_id: int
    doctor_id: int
    scheduled_time_min: int


@dataclass
class ScheduleResult:
    assignments: list[Assignment] = field(default_factory=list)
    unassigned_patient_ids: list[int] = field(default_factory=list)
    objective_value: float = 0.0


def optimize(patients: list[Patient], doctors: list[Doctor]) -> ScheduleResult:
    # Mutable per-doctor state: next available slot + remaining capacity for the day.
    state = {
        d.id: {"next_available": d.working_start_min, "remaining": d.max_daily_patients}
        for d in doctors
    }

    result = ScheduleResult()

    # No sort by urgency — original input order stands. This is the entire
    # difference from the C++ version's priority ordering.
    max_working_end = max((d.working_end_min for d in doctors), default=0)
    for patient in patients:
        eligible = [
            d for d in doctors
            if not patient.preferred_specialization
            or d.specialization == patient.preferred_specialization
        ]

        best_doctor = None
        best_time = None
        for d in eligible:
            s = state[d.id]
            if s["remaining"] <= 0:
                continue
            if s["next_available"] + SLOT_DURATION_MIN > d.working_end_min:
                continue
            if best_time is None or s["next_available"] < best_time:
                best_time = s["next_available"]
                best_doctor = d

        if best_doctor is None:
            result.unassigned_patient_ids.append(patient.id)
            result.objective_value += patient.urgency_level * max_working_end
            continue

        scheduled_time = state[best_doctor.id]["next_available"]
        result.assignments.append(Assignment(patient.id, best_doctor.id, scheduled_time))
        result.objective_value += patient.urgency_level * scheduled_time

        state[best_doctor.id]["next_available"] += SLOT_DURATION_MIN
        state[best_doctor.id]["remaining"] -= 1

    return result