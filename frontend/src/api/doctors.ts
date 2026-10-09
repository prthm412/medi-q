import { apiClient } from "./client";
import type { Doctor, AvailabilityResponse, Appointment } from "@/types";

export async function getMyDoctorProfile(): Promise<Doctor> {
  const response = await apiClient.get<Doctor>("/doctors/me");
  return response.data;
}

export async function listDoctors(): Promise<Doctor[]> {
  const response = await apiClient.get<Doctor[]>("/doctors");
  return response.data;
}

export async function getDoctorAvailability(doctorId: string, date: string): Promise<AvailabilityResponse> {
  const response = await apiClient.get<AvailabilityResponse>(`/doctors/${doctorId}/availability`, {
    params: { date },
  });
  return response.data;
}

export async function getMyDoctorAppointments(): Promise<Appointment[]> {
  const response = await apiClient.get<Appointment[]>("/doctors/me/appointments");
  return response.data;
}