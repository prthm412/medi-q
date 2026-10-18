import { apiClient } from "./client";
import axios from "axios";

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

export async function getQueuePosition(appointmentId: string): Promise<CheckInResponse | null> {
  try {
    const response = await apiClient.get<CheckInResponse>(`/queue/position/${appointmentId}`);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response?.status === 404) return null;
    throw error;
  }
}