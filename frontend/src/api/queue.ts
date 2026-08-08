import { apiClient } from "./client";

interface CheckInResponse {
  patient_id: string;
  position: number;
  estimated_wait_minutes: number;
}

export async function checkIn(appointmentId: string): Promise<CheckInResponse> {
  const response = await apiClient.post<CheckInResponse>("/queue/checkin", {
    appointment_id: appointmentId,
  });
  return response.data;
}