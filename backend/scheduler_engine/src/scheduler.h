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
        double objective_value;     // sum of urgency level * scheduled_time_min over assignments
    };

    ScheduleResult optimize(std::vector<Patient> patients, std::vector<Doctor> doctors);
}