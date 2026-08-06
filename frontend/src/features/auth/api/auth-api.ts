import { httpClient } from "@/services/http-client";

export interface UserSummary {
  id: string;
  email: string;
  fullName: string;
  isSuperadmin: boolean;
}

export interface PermissionSummary {
  module: string;
  action: string;
}

export interface IdentityResponse {
  user: UserSummary;
  permissions: PermissionSummary[];
}

export interface LoginPayload {
  email: string;
  password: string;
}

export const authApi = {
  login: (payload: LoginPayload) =>
    httpClient.post<IdentityResponse>("/api/auth/login", payload),
  me: () => httpClient.get<IdentityResponse>("/api/auth/me"),
  logout: () => httpClient.post<void>("/api/auth/logout"),
};
