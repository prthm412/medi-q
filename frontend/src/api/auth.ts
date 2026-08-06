import { apiClient } from "./client";
import type { User, UserRole } from "@/types";

interface LoginResponse {
  access_token: string;
  token_type: string;
}

export async function login(email: string, password: string): Promise<string> {
  const response = await apiClient.post<LoginResponse>("/auth/login", { email, password });
  return response.data.access_token;
}

export async function signup(email: string, password: string, role: UserRole): Promise<User> {
  const response = await apiClient.post<User>("/auth/signup", { email, password, role });
  return response.data;
}