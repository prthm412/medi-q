import { apiClient } from "./client";
import type { Patient, Appointment } from "@/types";

export async function getMyPatientProfile(): Promise<Patient> {
  const response = await apiClient.get<Patient>("/patients/me");
  return response.data;
}

export async function getPatientAppointments(patientId: string): Promise<Appointment[]> {
  const response = await apiClient.get<Appointment[]>(`/patients/${patientId}/appointments`);
  return response.data;
}