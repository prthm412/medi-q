"""
Benchmark: C++ greedy scheduler (scheduler_engine) vs. naive Python FCFS
baseline (baseline.py), on identical synthetic data.

Run from backend/:
    python scheduler_engine/benchmark/benchmark.py --patients 200 --doctors 10 --trials 5
"""

import argparse
import random
import sys
import time
from pathlib import Path
from statistics import mean


THIS_DIR = Path(__file__).resolve().parent
SCHEDULER_ENGINE_DIR = THIS_DIR.parent
BACKEND_DIR = SCHEDULER_ENGINE_DIR.parent

sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(SCHEDULER_ENGINE_DIR))

import scheduler_engine as cpp_engine  # the compiled .so
import baseline as py_baseline          # naive FCFS

SPECIALIZATIONS = ["general", "cardiology", "pediatrics", "orthopedics", "dermatology"]
WORKING_START_MIN = 540   # 09:00
WORKING_END_MIN = 1020    # 17:00


def generate_doctors(num_doctors: int, rng: random.Random) -> list[dict]:
    doctors = []
    for i in range(num_doctors):
        doctors.append({
            "id": i + 1,
            "specialization": SPECIALIZATIONS[i % len(SPECIALIZATIONS)],
            "working_start_min": WORKING_START_MIN,
            "working_end_min": WORKING_END_MIN,
            "max_daily_patients": rng.randint(15, 20),
        })
    return doctors


def generate_patients(num_patients: int, rng: random.Random) -> list[dict]:
    patients = []
    for i in range(num_patients):
        urgency = rng.choices([1, 2, 3, 4, 5], weights=[30, 25, 20, 15, 10])[0]
        # 90% of patients need a specific specialization; 10% have no preference
        pref = rng.choice(SPECIALIZATIONS) if rng.random() < 0.9 else ""
        patients.append({
            "id": i + 1,
            "urgency_level": urgency,
            "wait_minutes": rng.randint(0, 180),
            "preferred_specialization": pref,
        })
    return patients


def build_cpp_objects(patients_raw, doctors_raw):
    patients = [cpp_engine.Patient(**p) for p in patients_raw]
    doctors = [cpp_engine.Doctor(**d) for d in doctors_raw]
    return patients, doctors


def build_py_objects(patients_raw, doctors_raw):
    patients = [py_baseline.Patient(**p) for p in patients_raw]
    doctors = [py_baseline.Doctor(**d) for d in doctors_raw]
    return patients, doctors


def time_runs(optimize_fn, patients, doctors, trials: int):
    timings_ms = []
    result = None
    for _ in range(trials):
        start = time.perf_counter()
        result = optimize_fn(patients, doctors)
        timings_ms.append((time.perf_counter() - start) * 1000)
    return timings_ms, result


def main():
    parser = argparse.ArgumentParser(description="Benchmark C++ optimizer vs naive Python baseline")
    parser.add_argument("--patients", type=int, default=200)
    parser.add_argument("--doctors", type=int, default=10)
    parser.add_argument("--trials", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    doctors_raw = generate_doctors(args.doctors, rng)
    patients_raw = generate_patients(args.patients, rng)

    cpp_patients, cpp_doctors = build_cpp_objects(patients_raw, doctors_raw)
    py_patients, py_doctors = build_py_objects(patients_raw, doctors_raw)

    py_timings, py_result = time_runs(py_baseline.optimize, py_patients, py_doctors, args.trials)
    cpp_timings, cpp_result = time_runs(cpp_engine.optimize, cpp_patients, cpp_doctors, args.trials)

    def summarize(label, timings, result):
        print(f"\n--- {label} ---")
        print(f"Runtime (ms): mean={mean(timings):.3f}  min={min(timings):.3f}  max={max(timings):.3f}  (n={len(timings)} trials)")
        print(f"Assigned: {len(result.assignments)}  Unassigned: {len(result.unassigned_patient_ids)}")
        print(f"Objective value (sum urgency * scheduled_time_min): {result.objective_value:.2f}")
        if result.assignments:
            avg_scheduled = mean(a.scheduled_time_min for a in result.assignments)
            print(f"Average scheduled_time_min across assigned patients: {avg_scheduled:.2f}")

    print(f"Synthetic dataset: {args.patients} patients, {args.doctors} doctors, seed={args.seed}")
    summarize("Naive Python (FCFS)", py_timings, py_result)
    summarize("C++ greedy optimizer", cpp_timings, cpp_result)

    if py_result.objective_value > 0:
        reduction_pct = (1 - cpp_result.objective_value / py_result.objective_value) * 100
        print(f"\nObjective value reduction (C++ vs naive): {reduction_pct:.1f}%")
    if mean(py_timings) > 0:
        speedup = mean(py_timings) / mean(cpp_timings)
        print(f"Runtime speedup (C++ vs naive): {speedup:.1f}x")


if __name__ == "__main__":
    main()