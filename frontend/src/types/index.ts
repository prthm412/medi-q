export type UserRole = "patient" | "doctor" | "admin";

export interface User {
  id: string;
  email: string;
  role: UserRole;
}

export type AppointmentStatus = "scheduled" | "in_progress" | "completed" | "no_show";

export interface Doctor {
  id: string;
  user_id: string;
  name: string;
  specialization: string;
  working_hours_start: string;
  working_hours_end: string;
  max_daily_patients: number;
}

export interface Patient {
  id: string;
  user_id: string;
  name: string;
  dob: string;
  contact_info: string;
}

export interface Appointment {
  id: string;
  patient_id: string;
  doctor_id: string;
  room_id: number;
  scheduled_time: string;
  status: AppointmentStatus;
  urgency_level: number;
  created_at: string;
}

export interface AvailabilityResponse {
  doctor_id: string;
  date: string;
  available_slots: string[];
}

export interface ScheduleAssignment {
  patient_id: string;
  doctor_id: string;
  room_id: number;
  scheduled_time: string;
}

export interface ScheduleOptimizeResponse {
  date: string;
  assignments: ScheduleAssignment[];
  unassigned_patient_ids: string[];
  objective_value: number;
}

export interface QueuePositionUpdate {
  type: "position_update";
  patient_id: string;
  position: number;
  estimated_wait_minutes: number;
}

export interface MedicalRecord {
  id: string;
  patient_id: string;
  doctor_id: string;
  appointment_id: string | null;
  notes: string;
  created_at: string;
}

export interface AuditLogEntry {
  id: string;
  user_id: string;
  action: string;
  target_table: string;
  target_id: string;
  timestamp: string;
}