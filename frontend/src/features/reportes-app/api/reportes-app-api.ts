import { httpClient } from "@/services/http-client";
import type { Page } from "@/shared/types/pagination";

export type TipoReporte = "error" | "mejora";
export type EstadoReporte =
  "nuevo" | "propuesto" | "aprobado" | "en_curso" | "resuelto" | "descartado";
export type Decision = "aprobar" | "pedir_cambios" | "descartar";

/** Un reporte tal como llegó, más la propuesta de Claude (`nota`) y el
 * comentario del superadmin (`respuesta`). */
export interface Reporte {
  id: string;
  tipo: TipoReporte;
  estado: EstadoReporte;
  ruta: string;
  detalle: string;
  tiene_foto: boolean;
  nota: string | null;
  respuesta: string | null;
  usuario: string | null;
  creado_en: string;
  actualizado_en: string | null;
}

const BASE = "/api/reportes-app";

export const reportesAppApi = {
  crear: (datos: {
    tipo: TipoReporte;
    detalle: string;
    ruta: string;
    foto: File | null;
  }) => {
    const form = new FormData();
    form.append("tipo", datos.tipo);
    form.append("detalle", datos.detalle);
    form.append("ruta", datos.ruta);
    if (datos.foto) form.append("foto", datos.foto);
    return httpClient.postForm<{ id: string }>(BASE, form);
  },
  listar: (estado: EstadoReporte | null, page: number, size: number) => {
    const q = new URLSearchParams({ page: String(page), size: String(size) });
    if (estado) q.set("estado", estado);
    return httpClient.get<Page<Reporte>>(`${BASE}?${q.toString()}`);
  },
  fotoUrl: (id: string) => `${BASE}/${id}/foto`,
  decidir: (id: string, decision: Decision, respuesta: string | null) =>
    httpClient.post<void>(`${BASE}/${id}/decision`, { decision, respuesta }),
};
