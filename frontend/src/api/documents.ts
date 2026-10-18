import { apiClient } from "./client";

export async function downloadPrescription(appointmentId: string): Promise<void> {
  const response = await apiClient.get(`/documents/${appointmentId}/prescription`, {
    responseType: "blob",
  });
  const url = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = `prescription-${appointmentId}.pdf`;
  link.click();
  URL.revokeObjectURL(url);
}