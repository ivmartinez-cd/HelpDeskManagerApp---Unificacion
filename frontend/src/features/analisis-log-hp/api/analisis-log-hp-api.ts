import { httpClient } from "@/services/http-client";
import type {
  AiDiagnoseResult,
  AnalysisResult,
  ClientDevice,
  DeviceHealth,
  ErrorCode,
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

  getAlerts: (deviceId: number) =>
    httpClient.get<Record<string, unknown>[]>(`${BASE_SDS}/devices/${deviceId}/alerts`),

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
