import { httpClient } from "@/services/http-client";

export interface UserSummary {
  id: string;
  email: string;
  fullName: string;
  isSuperadmin: boolean;
  color: string | null;
}

export interface PermissionSummary {
  module: string;
  action: string;
}

export interface IdentityResponse {
  user: UserSummary;
  permissions: PermissionSummary[];
}

export interface ModuleSummary {
  key: string;
  label: string;
  route: string;
  icon: string;
  sortOrder: number;
  isEnabled: boolean;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export const authApi = {
  login: (payload: LoginPayload) =>
    httpClient.post<IdentityResponse>("/api/auth/login", payload),
  me: () => httpClient.get<IdentityResponse>("/api/auth/me"),
  modules: () => httpClient.get<ModuleSummary[]>("/api/auth/modules"),
  logout: () => httpClient.post<void>("/api/auth/logout"),
  forgotPassword: (email: string) =>
    httpClient.post<{ message: string }>("/api/auth/password/forgot", { email }),
  resetPassword: (token: string, newPassword: string) =>
    httpClient.post<void>("/api/auth/password/reset", { token, newPassword }),
  changePassword: (currentPassword: string, newPassword: string) =>
    httpClient.post<void>("/api/auth/password/change", { currentPassword, newPassword }),
};
