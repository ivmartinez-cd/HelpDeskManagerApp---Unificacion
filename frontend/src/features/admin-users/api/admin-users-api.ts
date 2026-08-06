import { httpClient } from "@/services/http-client";

export interface AdminUser {
  id: string;
  email: string;
  fullName: string;
  isActive: boolean;
  isSuperadmin: boolean;
  createdAt: string;
}

export interface PaginatedUsers {
  items: AdminUser[];
  total: number;
  page: number;
  size: number;
}

export interface CreateUserPayload {
  email: string;
  fullName: string;
}

export interface UpdateUserPayload {
  fullName?: string;
  isActive?: boolean;
}

export const adminUsersApi = {
  list: (params: { page: number; size: number; q?: string }) => {
    const query = new URLSearchParams({
      page: String(params.page),
      size: String(params.size),
    });
    if (params.q) query.set("q", params.q);
    return httpClient.get<PaginatedUsers>(`/api/admin/users?${query.toString()}`);
  },
  get: (id: string) => httpClient.get<AdminUser>(`/api/admin/users/${id}`),
  create: (payload: CreateUserPayload) =>
    httpClient.post<AdminUser>("/api/admin/users", payload),
  update: (id: string, payload: UpdateUserPayload) =>
    httpClient.patch<AdminUser>(`/api/admin/users/${id}`, payload),
  triggerPasswordReset: (id: string) =>
    httpClient.post<{ message: string }>(`/api/admin/users/${id}/password-reset`),
};
