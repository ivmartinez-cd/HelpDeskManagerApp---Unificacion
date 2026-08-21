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
  /** Funciones (pantallas/cards) concedidas por usuario, por clave (ADR-032). */
  features?: string[];
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

/** Envelope `Page[T]` del backend — declarado local, como en el resto de las
 * features (no hay tipo compartido para no acoplarlas). */
export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export const authApi = {
  login: (payload: LoginPayload) =>
    httpClient.post<IdentityResponse>("/api/auth/login", payload),
  me: () => httpClient.get<IdentityResponse>("/api/auth/me"),
  modules: () =>
    httpClient.get<Page<ModuleSummary>>("/api/auth/modules").then((p) => p.items),
  logout: () => httpClient.post<void>("/api/auth/logout"),
  forgotPassword: (email: string) =>
    httpClient.post<{ message: string }>("/api/auth/password/forgot", { email }),
  resetPassword: (token: string, newPassword: string) =>
    httpClient.post<void>("/api/auth/password/reset", { token, newPassword }),
  changePassword: (currentPassword: string, newPassword: string) =>
    httpClient.post<void>("/api/auth/password/change", { currentPassword, newPassword }),
};
