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

/** Función (pantalla/card) concedible por usuario, además de las acciones
 * (ADR-032). Se agrupa bajo su módulo en la grilla. */
export interface FeatureCatalogItem {
  key: string;
  module: string;
  label: string;
  description: string;
  sortOrder: number;
}

export interface PermissionItem {
  module: string;
  action: string;
}

export interface PermissionsResponse {
  grants: PermissionItem[];
}

export interface FeaturesResponse {
  features: string[];
}

/** Envelope `Page[T]` del backend — declarado local, como en el resto de las
 * features (no hay tipo compartido para no acoplarlas). */
interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export const adminPermissionsApi = {
  modules: () =>
    httpClient.get<Page<ModuleCatalogItem>>("/api/admin/catalog/modules").then((p) => p.items),
  actions: () =>
    httpClient.get<Page<ActionCatalogItem>>("/api/admin/catalog/actions").then((p) => p.items),
  features: () =>
    httpClient.get<Page<FeatureCatalogItem>>("/api/admin/catalog/features").then((p) => p.items),
  getUserPermissions: (userId: string) =>
    httpClient.get<PermissionsResponse>(`/api/admin/users/${userId}/permissions`),
  replaceUserPermissions: (userId: string, grants: PermissionItem[]) =>
    httpClient.put<PermissionsResponse>(`/api/admin/users/${userId}/permissions`, { grants }),
  getUserFeatures: (userId: string) =>
    httpClient.get<FeaturesResponse>(`/api/admin/users/${userId}/features`),
  replaceUserFeatures: (userId: string, features: string[]) =>
    httpClient.put<FeaturesResponse>(`/api/admin/users/${userId}/features`, { features }),
};
