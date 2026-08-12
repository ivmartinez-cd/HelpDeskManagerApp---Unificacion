import { httpClient } from "@/services/http-client";
import type {
  ImportarLiquidacionResult,
  Liquidacion,
  LiquidacionPage,
  PrestadorLiquidacion,
} from "../types/liquidaciones";

export const liquidacionesApi = {
  listPrestadores: (soloActivos = true) =>
    httpClient.get<PrestadorLiquidacion[]>(
      `/api/liquidaciones/prestadores?soloActivos=${soloActivos}`,
    ),

  list: (params?: { prestadorId?: string; page?: number; size?: number }) => {
    const qs = new URLSearchParams();
    if (params?.prestadorId) qs.set("prestadorId", params.prestadorId);
    qs.set("page", String(params?.page ?? 1));
    qs.set("size", String(params?.size ?? 50));
    return httpClient.get<LiquidacionPage>(`/api/liquidaciones?${qs}`);
  },

  get: (id: string) => httpClient.get<Liquidacion>(`/api/liquidaciones/${id}`),

  importar: (prestadorId: string, file: File) => {
    const fd = new FormData();
    fd.append("prestadorId", prestadorId);
    fd.append("file", file);
    return httpClient.postForm<ImportarLiquidacionResult>("/api/liquidaciones/importar", fd);
  },

  reanalyze: (id: string) =>
    httpClient.post<{ totalIncidentes: number; totalAlertas: number; totalObservaciones: number }>(
      `/api/liquidaciones/${id}/reanalyze`,
    ),
};
