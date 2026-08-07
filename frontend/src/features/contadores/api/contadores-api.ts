import { httpClient } from "@/services/http-client";

export interface ProyeccionResponse {
  xlsx_filename: string;
  csv_filename: string;
  total_series: number;
  series_proyectadas: number;
  series_sin_datos: number;
  series_reales: number;
}

export interface ManualEstimationRequest {
  contador_inicial: number;
  contador_final: number;
  fecha_inicial: string;
  fecha_final: string;
  fecha_estimacion: string;
}

export interface ManualEstimationResponse {
  dias_muestra: number;
  consumo_muestra: number;
  consumo_diario: number;
  dias_estimados: number;
  contador_estimado: number;
}

export interface Db3ExportResponse {
  csv_filename: string;
  total_rows: number;
  counterclass_40_count: number;
  counterclass_10_count: number;
  counterclass_20_count: number;
}

export interface EstimationZeroResponse {
  csv_filename: string;
  total_rows: number;
}

export interface FixedSumResponse {
  csv_filenames: string[];
  total_rows: number;
}

export interface FtpClient {
  id: string;
  name: string;
  host: string;
  port: number;
  username: string;
  remote_dir: string;
  created_at: string;
  updated_at: string;
}

export interface CreateFtpClientPayload {
  name: string;
  host: string;
  port?: number;
  username: string;
  password?: string;
  remote_dir?: string;
}

export interface UpdateFtpClientPayload {
  name?: string;
  host?: string;
  port?: number;
  username?: string;
  password?: string;
  remote_dir?: string;
}

export interface ProcessFtpClientResponse {
  csv_filename: string;
  total_rows: number;
}

export interface SdsClient {
  id: string;
  name: string;
  suma_color: boolean;
}

export interface UpdateSdsConfigPayload {
  customer_name: string;
  suma_color: boolean;
}

export interface ProcessSdsResponse {
  csv_filename: string;
  customer_name: string;
}

export interface ErsClient {
  id: string;
  name: string;
  suma_color: boolean;
}

export interface UpdateErsConfigPayload {
  customer_name: string;
  suma_color: boolean;
}

export interface ProcessErsResponse {
  csv_filename: string;
  customer_name: string;
}

export const contadoresApi = {
  // Proyección
  runProyeccion: (formData: FormData) =>
    httpClient.postForm<ProyeccionResponse>("/api/contadores/proyeccion", formData),

  // Calculadora manual
  runManualEstimation: (payload: ManualEstimationRequest) =>
    httpClient.post<ManualEstimationResponse>("/api/contadores/calc", payload),

  // DB3 a CSV
  runDb3Export: (formData: FormData) =>
    httpClient.postForm<Db3ExportResponse>("/api/contadores/db3", formData),

  // Estimación en 0
  runEstimationZero: (formData: FormData) =>
    httpClient.postForm<EstimationZeroResponse>("/api/contadores/en0", formData),

  // Suma Fija
  runFixedSum: (formData: FormData) =>
    httpClient.postForm<FixedSumResponse>("/api/contadores/suma-fija", formData),

  // Clientes FTP
  listFtpClients: () => httpClient.get<FtpClient[]>("/api/contadores/ftp/clients"),
  getFtpClient: (id: string) => httpClient.get<FtpClient>(`/api/contadores/ftp/clients/${id}`),
  createFtpClient: (payload: CreateFtpClientPayload) =>
    httpClient.post<FtpClient>("/api/contadores/ftp/clients", payload),
  updateFtpClient: (id: string, payload: UpdateFtpClientPayload) =>
    httpClient.put<FtpClient>(`/api/contadores/ftp/clients/${id}`, payload),
  deleteFtpClient: (id: string) =>
    httpClient.delete<{ message: string }>(`/api/contadores/ftp/clients/${id}`),
  processFtpClient: (id: string, fechaMaxima?: string) =>
    httpClient.post<ProcessFtpClientResponse>(
      `/api/contadores/ftp/clients/${id}/process`,
      fechaMaxima ? { fecha_maxima: fechaMaxima } : {},
    ),

  // HP SDS
  listSdsClients: () => httpClient.get<SdsClient[]>("/api/contadores/sds/clients"),
  updateSdsConfig: (id: string, payload: UpdateSdsConfigPayload) =>
    httpClient.put<SdsClient>(`/api/contadores/sds/clients/${id}/config`, payload),
  processSds: (payload: { customer_id: string; customer_name: string; fecha_maxima: string }) =>
    httpClient.post<ProcessSdsResponse>("/api/contadores/sds/process", payload),

  // Epson ERS
  listErsClients: () => httpClient.get<ErsClient[]>("/api/contadores/ers/clients"),
  updateErsConfig: (id: string, payload: UpdateErsConfigPayload) =>
    httpClient.put<ErsClient>(`/api/contadores/ers/clients/${id}/config`, payload),
  processErs: (payload: { customer_id: string; customer_name: string; fecha_maxima: string }) =>
    httpClient.post<ProcessErsResponse>("/api/contadores/ers/process", payload),

  // Download Output File
  getOutputUrl: (filename: string) => `/api/contadores/outputs/${encodeURIComponent(filename)}`,
};
