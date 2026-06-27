#include "scheduler.h"

#include <algorithm>
#include <queue>
#include <unordered_map>

namespace scheduler_engine {

    namespace {

        struct DoctorSlot {
            int next_available_min;
            int doctor_id;
            int working_end_min;
            int remaining_capacity;
        };

        struct CompareSlot {
            // std::priority_queue is a max-heap by default; flipping the comparison
            // turns it into a min-heap ordered by earliest next-available time.
            bool operator()(const DoctorSlot& a, const DoctorSlot& b) const {
                return a.next_available_min > b.next_available_min;
            }
        };

        using SlotHeap = std::priority_queue<DoctorSlot, std::vector<DoctorSlot>, CompareSlot>;

    }

    ScheduleResult optimize(std::vector<Patient> patients, std::vector<Doctor> doctors) {
        // One min-heap per specialization, seeded with every doctor of that specialization
        // starting at their working_start_min with full daily capacity.
        std::unordered_map<std::string, SlotHeap> heaps;
        for (const auto& doc : doctors) {
            heaps[doc.specialization].push(DoctorSlot{
                doc.working_start_min, doc.id, doc.working_end_min, doc.max_daily_patients
            });
        }

        // Priority order: highest urgency first, then longest-waiting first as a tie-break.
        std::sort(patients.begin(), patients.end(), [](const Patient& a, const Patient& b) {
            if (a.urgency_level != b.urgency_level) return a.urgency_level > b.urgency_level;
            return a.wait_minutes > b.wait_minutes;
        });

        ScheduleResult result;
        result.objective_value = 0.0;

        for (const auto& patient : patients) {
            std::vector<std::string> candidate_specs;
            if (!patient.preferred_specialization.empty()) {
                candidate_specs.push_back(patient.preferred_specialization);
            } else {
                for (const auto& kv : heaps) candidate_specs.push_back(kv.first);
            }

            bool found = false;
            std::string best_spec;
            DoctorSlot best_slot{};

            for (const auto& spec : candidate_specs) {
                auto it = heaps.find(spec);
                if (it == heaps.end() || it->second.empty()) continue;
                const DoctorSlot& top = it->second.top();
                if (!found || top.next_available_min < best_slot.next_available_min) {
                    found = true;
                    best_spec = spec;
                    best_slot = top;
                }
            }

            if (!found) {
                result.unassigned_patient_ids.push_back(patient.id);
                continue;
            }

            heaps[best_spec].pop();

            int scheduled_time = best_slot.next_available_min;
            result.assignments.push_back(Assignment{patient.id, best_slot.doctor_id, scheduled_time});
            result.objective_value += static_cast<double>(patient.urgency_level) * scheduled_time;

            int new_next = scheduled_time + SLOT_DURATION_MIN;
            int new_capacity = best_slot.remaining_capacity - 1;
            if (new_capacity > 0 && new_next + SLOT_DURATION_MIN <= best_slot.working_end_min) {
                heaps[best_spec].push(DoctorSlot{
                    new_next, best_slot.doctor_id, best_slot.working_end_min, new_capacity
                });
            }
            // else: this doctor has no more room today, so they simply don't go back in the heap.
        }
        return result;
    }
}
