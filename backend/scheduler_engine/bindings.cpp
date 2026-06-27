#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "src/scheduler.h"

namespace py = pybind11;
using namespace scheduler_engine;

PYBIND11_MODULE(scheduler_engine, m) {
    m.doc() = "Greedy list-scheduling optimizer for multi-doctor appointment assignment";

    py::class_<Doctor>(m, "Doctor")
        .def(py::init([](int id, std::string specialization, int start, int end, int max_patients) {
            return Doctor{id, specialization, start, end, max_patients};
        }), py::arg("id"), py::arg("specialization"), py::arg("working_start_min"),
            py::arg("working_end_min"), py::arg("max_daily_patients"))
        .def_readwrite("id", &Doctor::id)
        .def_readwrite("specialization", &Doctor::specialization)
        .def_readwrite("working_start_min", &Doctor::working_start_min)
        .def_readwrite("working_end_min", &Doctor::working_end_min)
        .def_readwrite("max_daily_patients", &Doctor::max_daily_patients);

    py::class_<Patient>(m, "Patient")
        .def(py::init([](int id, int urgency, int wait, std::string spec) {
            return Patient{id, urgency, wait, spec};
        }), py::arg("id"), py::arg("urgency_level"), py::arg("wait_minutes"),
            py::arg("preferred_specialization") = "")
        .def_readwrite("id", &Patient::id)
        .def_readwrite("urgency_level", &Patient::urgency_level)
        .def_readwrite("wait_minutes", &Patient::wait_minutes)
        .def_readwrite("preferred_specialization", &Patient::preferred_specialization);

    py::class_<Assignment>(m, "Assignment")
        .def_readonly("patient_id", &Assignment::patient_id)
        .def_readonly("doctor_id", &Assignment::doctor_id)
        .def_readonly("scheduled_time_min", &Assignment::scheduled_time_min);

    py::class_<ScheduleResult>(m, "ScheduleResult")
        .def_readonly("assignments", &ScheduleResult::assignments)
        .def_readonly("unassigned_patient_ids", &ScheduleResult::unassigned_patient_ids)
        .def_readonly("objective_value", &ScheduleResult::objective_value);

    m.def("optimize", &optimize, py::arg("patients"), py::arg("doctors"),
          "Assign patients to (doctor, time-slot) pairs minimizing urgency-weighted delay");
}