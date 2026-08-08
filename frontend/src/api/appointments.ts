import { apiClient } from "./client";
import type { Appointment, AppointmentStatus } from "@/types";

interface CreateAppointmentPayload {
  patient_id: string;
  doctor_id: string;
  room_id: number;
  scheduled_time: string;
  urgency_level: number;
}

export async function createAppointment(payload: CreateAppointmentPayload): Promise<Appointment> {
  const response = await apiClient.post<Appointment>("/appointments", payload);
  return response.data;
}

export async function updateAppointmentStatus(
  appointmentId: string,
  status: AppointmentStatus
): Promise<Appointment> {
  const response = await apiClient.patch<Appointment>(`/appointments/${appointmentId}/status`, { status });
  return response.data;
}