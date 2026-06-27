import random

import scheduler_engine as se


def _make_doctors(specs_and_counts, working_start=540, working_end=1020, capacity=15):
    """specs_and_counts: list of (specialization, count) pairs."""
    doctors = []
    doctor_id = 1
    for spec, count in specs_and_counts:
        for _ in range(count):
            doctors.append(se.Doctor(
                id=doctor_id,
                specialization=spec,
                working_start_min=working_start,
                working_end_min=working_end,
                max_daily_patients=capacity,
            ))
            doctor_id += 1
    return doctors


def _random_patients(n, specs, rng):
    patients = []
    for i in range(n):
        urgency = rng.randint(1, 5)
        wait = rng.randint(0, 180)
        pref = rng.choice(specs) if rng.random() < 0.9 else ""
        patients.append(se.Patient(
            id=i + 1, urgency_level=urgency, wait_minutes=wait, preferred_specialization=pref
        ))
    return patients


def test_no_doctor_double_booked():
    """No doctor is ever assigned two patients at the same scheduled_time_min."""
    rng = random.Random(7)
    specs = ["general", "cardiology", "pediatrics"]
    doctors = _make_doctors([(s, 2) for s in specs], capacity=10)
    patients = _random_patients(80, specs, rng)

    result = se.optimize(patients, doctors)

    by_doctor: dict[int, list[int]] = {}
    for a in result.assignments:
        by_doctor.setdefault(a.doctor_id, []).append(a.scheduled_time_min)

    for doctor_id, times in by_doctor.items():
        assert len(times) == len(set(times)), (
            f"Doctor {doctor_id} has overlapping appointments: {sorted(times)}"
        )


def test_specialization_never_violated():
    """A patient with a preferred specialization is never assigned to a
    doctor outside that specialization."""
    rng = random.Random(11)
    specs = ["general", "cardiology", "pediatrics", "orthopedics"]
    doctors = _make_doctors([(s, 2) for s in specs], capacity=10)
    doctor_spec = {d.id: d.specialization for d in doctors}
    patients = _random_patients(100, specs, rng)
    patient_pref = {p.id: p.preferred_specialization for p in patients}

    result = se.optimize(patients, doctors)

    for a in result.assignments:
        pref = patient_pref[a.patient_id]
        if pref:
            assert doctor_spec[a.doctor_id] == pref, (
                f"Patient {a.patient_id} wanted '{pref}' but was assigned to "
                f"doctor {a.doctor_id} ('{doctor_spec[a.doctor_id]}')"
            )


def test_higher_urgency_never_scheduled_later_when_arrived_same_time():
    """A higher-urgency patient is never scheduled later than a lower-urgency
    patient who arrived (same wait_minutes) needing the same type of doctor."""
    doctors = _make_doctors([("general", 1)], capacity=2)  # exactly 2 slots available today

    same_wait = 30
    patients = [
        se.Patient(id=1, urgency_level=2, wait_minutes=same_wait, preferred_specialization="general"),
        se.Patient(id=2, urgency_level=5, wait_minutes=same_wait, preferred_specialization="general"),
        se.Patient(id=3, urgency_level=4, wait_minutes=same_wait, preferred_specialization="general"),
    ]

    result = se.optimize(patients, doctors)
    scheduled = {a.patient_id: a.scheduled_time_min for a in result.assignments}

    # Highest urgency (id 2) gets the earliest slot, next-highest (id 3) gets
    # the next one -- same arrival time, strictly descending urgency produces
    # non-decreasing schedule times among the patients who get seen.
    assert scheduled[2] <= scheduled[3]

    # Only 2 daily slots for 3 tied-arrival-time patients -- the lowest-urgency
    # one (id 1) is the one left unassigned, confirming urgency (not arrival
    # order or patient id) drove the cut.
    assert 1 in result.unassigned_patient_ids
    assert 2 not in result.unassigned_patient_ids
    assert 3 not in result.unassigned_patient_ids


def test_doctor_capacity_never_exceeded():
    """Bonus check beyond the three required properties: no doctor is ever
    assigned more patients in a day than max_daily_patients."""
    rng = random.Random(19)
    specs = ["general", "cardiology"]
    doctors = _make_doctors([(s, 1) for s in specs], capacity=5)
    patients = _random_patients(50, specs, rng)

    result = se.optimize(patients, doctors)

    counts: dict[int, int] = {}
    for a in result.assignments:
        counts[a.doctor_id] = counts.get(a.doctor_id, 0) + 1

    capacity = {d.id: d.max_daily_patients for d in doctors}
    for doctor_id, count in counts.items():
        assert count <= capacity[doctor_id]