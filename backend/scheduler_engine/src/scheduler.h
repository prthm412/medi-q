#pragma once
#include <string>
#include <vector>

namespace scheduler_engine{
    constexpr int SLOT_DURATION_MIN = 20; // matches the availability-check endpoint's slot size

    struct Doctor {
        int id;
        std::string specialization;
        int working_start_min;  // minutes since midnight
        int working_end_min;
        int max_daily_patients;
    };

    struct Patient {
        int id;
        int urgency_level;      // 1-5, 5=most urgent
        int wait_minutes;       // tie-break only, not part of the objective
        std::string preferred_specialization;   // empty string means no preference -> any doctor available
    };

    struct Assignment {
        int patient_id;
        int doctor_id;
        int scheduled_time_min;
    };
    struct ScheduleResult {
        std::vector<Assignment> assignments;
        std::vector<int> unassigned_patient_ids;
        // Sum of urgency_level * scheduled_time_min over assignments, plus
        // urgency_level * max(doctor working_end_min) for each unassigned
        // patient - being unseen today is charged as at least as costly as
        // the worst possible same-day slot, so an algorithm can never improve
        // its score by leaving a patient unassigned instead of seeing them late.
        double objective_value; 
    };

    ScheduleResult optimize(std::vector<Patient> patients, std::vector<Doctor> doctors);
}