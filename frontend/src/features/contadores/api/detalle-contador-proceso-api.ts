import { httpClient } from "@/services/http-client";
import type { DetalleContadorProceso } from "../types/detalle-contador-proceso";

const BASE = "/api/contadores/detalle-proceso";

export type AlcanceReporte = "todos" | "falta_contador";

export const detalleContadorProcesoApi = {
  getDetalle: (nroProceso: number) =>
    httpClient.get<DetalleContadorProceso>(`${BASE}/${nroProceso}`),

  getDetallePorGrupo: (idGrupoEconomico: number) =>
    httpClient.get<DetalleContadorProceso>(`${BASE}/por-grupo/${idGrupoEconomico}`),

  getXlsxUrl: (nroProceso: number, alcance: AlcanceReporte) =>
    `${BASE}/${nroProceso}/xlsx?alcance=${alcance}`,
};
