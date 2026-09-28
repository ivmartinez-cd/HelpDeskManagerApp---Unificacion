import { httpClient } from "@/services/http-client";

/** Lo que queda de Administración > Usuarios tras la unificación en Personas
 * (ADR-040): la grilla de permisos lee la cuenta y la ficha manda el link de
 * restablecimiento. Alta, edición y listado de cuentas viven en Personas. */
export interface AdminUser {
  id: string;
  email: string;
  fullName: string;
  isActive: boolean;
  isSuperadmin: boolean;
  createdAt: string;
  color: string | null;
}

export const adminUsersApi = {
  get: (id: string) => httpClient.get<AdminUser>(`/api/admin/users/${id}`),
  triggerPasswordReset: (id: string) =>
    httpClient.post<{ message: string }>(`/api/admin/users/${id}/password-reset`),
};
