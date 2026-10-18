import { apiClient } from "./client";
import type { ScheduleOptimizeResponse } from "@/types";

export async function optimizeSchedule(date: string): Promise<ScheduleOptimizeResponse> {
  const response = await apiClient.post<ScheduleOptimizeResponse>("/schedule/optimize", { date });
  return response.data;
}