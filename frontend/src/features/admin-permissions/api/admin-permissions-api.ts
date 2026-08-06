import { httpClient } from "@/services/http-client";

export interface ModuleCatalogItem {
  key: string;
  label: string;
  route: string;
  icon: string;
  sortOrder: number;
  isEnabled: boolean;
  actions: string[];
}

export interface ActionCatalogItem {
  key: string;
  label: string;
}

export interface PermissionItem {
  module: string;
  action: string;
}

export interface PermissionsResponse {
  grants: PermissionItem[];
}

export const adminPermissionsApi = {
  modules: () => httpClient.get<ModuleCatalogItem[]>("/api/admin/catalog/modules"),
  actions: () => httpClient.get<ActionCatalogItem[]>("/api/admin/catalog/actions"),
  getUserPermissions: (userId: string) =>
    httpClient.get<PermissionsResponse>(`/api/admin/users/${userId}/permissions`),
  replaceUserPermissions: (userId: string, grants: PermissionItem[]) =>
    httpClient.put<PermissionsResponse>(`/api/admin/users/${userId}/permissions`, { grants }),
};
