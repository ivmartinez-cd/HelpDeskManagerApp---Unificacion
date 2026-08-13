import { httpClient } from "@/services/http-client";
import type { ReporteVacaciones } from "../types/vacaciones";

const BASE = "/api/vacaciones/reportes";

export const reportesApi = {
  getReporte: () => httpClient.get<ReporteVacaciones>(BASE),
  downloadExcel: () => httpClient.downloadFile(`${BASE}/excel`, "reporte-vacaciones.xlsx"),
  downloadPdf: () => httpClient.downloadFile(`${BASE}/pdf`, "reporte-vacaciones.pdf"),
};
