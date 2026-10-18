import { apiClient } from "./client";
import type { AnalyticsSummary } from "@/types";

export async function getAnalyticsSummary(days: number): Promise<AnalyticsSummary> {
  const response = await apiClient.get<AnalyticsSummary>("/analytics/summary", {
    params: { days },
  });
  return response.data;
}