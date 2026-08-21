import { httpClient } from "@/services/http-client";
import type {
  AiDiagnoseResult,
  AnalysisResult,
  CdsIncident,
  ClientDevice,
  DeviceHealth,
  ErrorCode,
  FleetClient,
  Incident,
  Page,
  ResolvedDevice,
  SavedAnalysis,
  SavedAnalysisDetail,
  SdsExtractResult,
} from "../types/analisis-log-hp";

const BASE = "/api/analisis-log-hp";
const BASE_SDS = `${BASE}/sds`;

export const analisisLogHpApi = {
  // SDS / Insight
  extractLogs: (serial: string, days = 30) =>
    httpClient.post<SdsExtractResult>(`${BASE_SDS}/extract-logs`, { serial, days }),

  resolveDevice: (serial: string) =>
    httpClient.get<ResolvedDevice | null>(`${BASE_SDS}/resolve-device?serial=${encodeURIComponent(serial)}`),

  getConsumables: (deviceId: number) =>
    httpClient.get<Record<string, unknown>[]>(`${BASE_SDS}/devices/${deviceId}/consumables`),

  getAlerts: (deviceId: number, currentOnly = true) =>
    httpClient.get<Record<string, unknown>[]>(
      `${BASE_SDS}/devices/${deviceId}/alerts?current_only=${currentOnly}`,
    ),

  getMeters: (deviceId: number, days = 90) =>
    httpClient.get<Record<string, unknown>[]>(`${BASE_SDS}/devices/${deviceId}/meters?days=${days}`),

  getRemoteEws: (deviceId: string) =>
    httpClient.get<{ url: string | null }>(`${BASE_SDS}/devices/${encodeURIComponent(deviceId)}/remote-ews`),

  getHpOperations: (deviceId: string) =>
    httpClient.get<Record<string, unknown>[]>(`${BASE_SDS}/devices/${encodeURIComponent(deviceId)}/hp-operations`),

  refreshCache: (deviceId: string) =>
    httpClient.post<{ baseline: Record<string, unknown>[] }>(`${BASE_SDS}/devices/${encodeURIComponent(deviceId)}/refresh-cache`),

  getClientDevices: (customerId: number) =>
    httpClient.get<ClientDevice[]>(`${BASE_SDS}/clients/${customerId}/devices`),

  listClients: () => httpClient.get<FleetClient[]>(`${BASE_SDS}/clients`),

  getCdsIncidents: (serial: string) =>
    httpClient
      .get<Page<CdsIncident>>(
        `${BASE_SDS}/devices/${encodeURIComponent(serial)}/cds-incidents?size=100`,
      )
      .then((p) => p.items),

  // CPMD
  getCpmdPdfUrl: (modelFamily: string) =>
    httpClient.get<{ url: string; label: string }>(
      `${BASE}/cpmd/pdf-url?model_family=${encodeURIComponent(modelFamily)}`,
    ),

  uploadCpmdManual: (file: File, keywords: string, label: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("keywords", keywords);
    form.append("label", label);
    return httpClient.postForm<{ id: number }>(`${BASE}/cpmd/upload`, form);
  },

  // Analysis
  previewAnalysis: (logs: string) =>
    httpClient.post<AnalysisResult>(`${BASE}/analysis/preview`, { logs }),

  aiDiagnose: (payload: Record<string, unknown>, model?: string) =>
    httpClient.post<AiDiagnoseResult>(`${BASE}/analysis/ai-diagnose`, {
      payload,
      ...(model ? { model } : {}),
    }),

  generatePdfSummary: (payload: Record<string, unknown>, model?: string) =>
    httpClient.post<AiDiagnoseResult>(`${BASE}/analysis/pdf-summary`, {
      payload,
      ...(model ? { model } : {}),
    }),

  // Error codes
  listErrorCodes: (page = 1, size = 50) =>
    httpClient.get<Page<ErrorCode>>(`${BASE}/error-codes?page=${page}&size=${size}`),

  upsertErrorCode: (data: {
    code: string;
    severity?: string;
    description?: string;
    solution_url?: string;
  }) => httpClient.post<ErrorCode>(`${BASE}/error-codes/upsert`, data),

  // Saved analyses
  listSavedAnalyses: (page = 1, size = 50) =>
    httpClient.get<Page<SavedAnalysis>>(`${BASE}/saved-analyses?page=${page}&size=${size}`),

  createSavedAnalysis: (data: {
    name: string;
    equipment_identifier?: string | null;
    incidents: Incident[];
    global_severity: string;
    ai_diagnosis?: string | null;
  }) => httpClient.post<SavedAnalysisDetail>(`${BASE}/saved-analyses`, data),

  getSavedAnalysis: (id: string) =>
    httpClient.get<SavedAnalysisDetail>(`${BASE}/saved-analyses/${id}`),

  deleteSavedAnalysis: (id: string) =>
    httpClient.delete<void>(`${BASE}/saved-analyses/${id}`),

  compareWithLog: (id: string, logs: string) =>
    httpClient.post<Record<string, unknown>>(`${BASE}/saved-analyses/${id}/compare`, { logs }),

  compareTwoSnapshots: (id: string, targetId: string) =>
    httpClient.get<Record<string, unknown>>(`${BASE}/saved-analyses/${id}/compare-with/${targetId}`),

  getDeviceHealth: (id: string) =>
    httpClient.get<DeviceHealth>(`${BASE}/saved-analyses/${id}/health`),
};
