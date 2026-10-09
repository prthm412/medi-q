import { apiClient } from "./client";
import type { MedicalRecord } from "@/types";

export async function getMedicalRecords(patientId: string): Promise<MedicalRecord[]> {
  const response = await apiClient.get<MedicalRecord[]>("/medical-records", {
    params: { patient_id: patientId },
  });
  return response.data;
}

export async function createMedicalRecord(appointmentId: string, notes: string): Promise<MedicalRecord> {
  const response = await apiClient.post<MedicalRecord>("/medical-records", {
    appointment_id: appointmentId,
    notes,
  });
  return response.data;
}