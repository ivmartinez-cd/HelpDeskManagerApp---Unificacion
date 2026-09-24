import { ApiError, httpClient } from "@/services/http-client";
import type { Page } from "@/shared/types/pagination";
import type {
  AccionBody,
  AceptarBody,
  AnexoOption,
  CandidatosEquipo,
  ContextoProceso,
  CrearRecesoBody,
  ForzarMetodoBody,
  GrupoEconomicoOption,
  HistorialEquipo,
  OpcionesExport,
  ProcesoOption,
  RecalcularCandidatoBody,
  RecalcularCandidatoResponse,
  Receso,
  SeleccionProcesoBody,
  SolicitudTableroReal,
  TableroProyeccion,
} from "../types/proyeccion";

const BASE = "/api/contadores/proyeccion";

function paramsSolicitud(solicitud: SolicitudTableroReal): URLSearchParams {
  return new URLSearchParams({
    nro_proceso: String(solicitud.nroProceso),
    id_grupo_economico: String(solicitud.idGrupoEconomico),
    id_anexo: String(solicitud.idAnexo),
    fecha_objetivo: solicitud.fechaObjetivo,
  });
}

/** Selección que viaja con cada acción del panel: en qué proceso se guarda
 * la decisión, contra qué grilla se calcula (sin proceso = ejemplo) y el
 * corte de "Descartar y empezar limpio" (la fila que muestra la grilla). */
export function seleccionBody({ solicitud, descartarHasta }: ContextoProceso): SeleccionProcesoBody {
  const corte = descartarHasta ? { descartar_hasta: descartarHasta } : {};
  if (!solicitud) return corte;
  return {
    nro_proceso: solicitud.nroProceso,
    id_grupo_economico: solicitud.idGrupoEconomico,
    id_anexo: solicitud.idAnexo,
    fecha_objetivo: solicitud.fechaObjetivo,
    ...corte,
  };
}

/** Mensaje legible de un error de la API (el `detail` de un 422/404), o el
 * texto de respaldo si no vino ninguno. */
export function mensajeError(err: unknown, respaldo: string): string {
  if (err instanceof ApiError && err.message) return err.message;
  return respaldo;
}

function nombreDeContentDisposition(header: string | null, respaldo: string): string {
  const match = header?.match(/filename="?([^";]+)"?/i);
  return match ? match[1] : respaldo;
}

async function descargarCsv(path: string, respaldo: string): Promise<void> {
  const res = await fetch(path, { credentials: "include" });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body ?? { message: "No se pudo generar el CSV.", code: "DOWNLOAD_ERROR" });
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nombreDeContentDisposition(res.headers.get("Content-Disposition"), respaldo);
  a.click();
  URL.revokeObjectURL(url);
}

export const proyeccionApi = {
  listGruposEconomicos: () =>
    httpClient
      .get<Page<GrupoEconomicoOption>>(`${BASE}/grupos-economicos`)
      .then((page) => page.items),

  listProcesos: (idGrupoEconomico: number) =>
    httpClient
      .get<Page<ProcesoOption>>(`${BASE}/procesos?id_grupo_economico=${idGrupoEconomico}`)
      .then((page) => page.items),

  listAnexos: (idGrupoEconomico: number) =>
    httpClient
      .get<Page<AnexoOption>>(`${BASE}/anexos?id_grupo_economico=${idGrupoEconomico}`)
      .then((page) => page.items),

  // Sin `solicitud`: tablero de ejemplo. `descartarHasta`: "Descartar y
  // empezar limpio" (se ignoran las decisiones guardadas hasta ese momento).
  getTablero: (solicitud: SolicitudTableroReal | undefined, descartarHasta: string | null) => {
    const qs = solicitud ? paramsSolicitud(solicitud) : new URLSearchParams();
    if (descartarHasta) qs.set("descartar_hasta", descartarHasta);
    const query = qs.toString();
    return httpClient.get<TableroProyeccion>(`${BASE}/tablero${query ? `?${query}` : ""}`);
  },

  getCandidatos: (idMaquina: number, clase: string, contexto: ContextoProceso) => {
    const qs = contexto.solicitud ? paramsSolicitud(contexto.solicitud) : new URLSearchParams();
    if (contexto.descartarHasta) qs.set("descartar_hasta", contexto.descartarHasta);
    const query = qs.toString();
    return httpClient.get<CandidatosEquipo>(`${BASE}/candidatos/${idMaquina}/${clase}${query ? `?${query}` : ""}`);
  },

  // Vista previa de una P/L manual: no guarda nada.
  recalcularCandidato: (body: RecalcularCandidatoBody) =>
    httpClient.post<RecalcularCandidatoResponse>(`${BASE}/candidatos/recalcular`, body),

  // "Usar T19 (cascada)" / "Usar entre reales": se guarda al toque.
  forzarMetodo: (body: ForzarMetodoBody) =>
    httpClient.post<RecalcularCandidatoResponse>(`${BASE}/candidatos/forzar`, body),

  marcarPendiente: (idMaquina: number, clase: string, body: AccionBody) =>
    httpClient.post<void>(`${BASE}/candidatos/${idMaquina}/${clase}/marcar-pendiente`, body),

  aceptar: (idMaquina: number, clase: string, body: AceptarBody) =>
    httpClient.post<void>(`${BASE}/candidatos/${idMaquina}/${clase}/aceptar`, body),

  listRecesos: (idGrupoEconomico?: number) => {
    const qs = idGrupoEconomico ? `?id_grupo_economico=${idGrupoEconomico}` : "";
    return httpClient.get<Page<Receso>>(`${BASE}/recesos${qs}`).then((page) => page.items);
  },

  crearReceso: (body: CrearRecesoBody) => httpClient.post<Receso>(`${BASE}/recesos`, body),

  // "Editar" de `Recesos.razor`: pisa todos los campos del receso.
  actualizarReceso: (id: number, body: CrearRecesoBody) => httpClient.put<Receso>(`${BASE}/recesos/${id}`, body),

  eliminarReceso: (id: number, idGrupoEconomico?: number) => {
    const qs = idGrupoEconomico ? `?id_grupo_economico=${idGrupoEconomico}` : "";
    return httpClient.delete<void>(`${BASE}/recesos/${id}${qs}`);
  },

  // Solo proceso real. El nombre del archivo lo decide el backend
  // (`Estimacion_{Nro}_{yyyyMMdd}[_estimados].csv`, como el legacy).
  exportarCsv: (solicitud: SolicitudTableroReal, opciones: OpcionesExport) => {
    const qs = paramsSolicitud(solicitud);
    qs.set("solo_estimados", String(opciones.soloEstimados));
    if (opciones.descartarHasta) qs.set("descartar_hasta", opciones.descartarHasta);
    const fecha = solicitud.fechaObjetivo.replaceAll("-", "");
    const sufijo = opciones.soloEstimados ? "_estimados" : "";
    return descargarCsv(`${BASE}/export?${qs.toString()}`, `Estimacion_${solicitud.nroProceso}_${fecha}${sufijo}.csv`);
  },

  // Línea de tiempo de un equipo — vacía para un equipo de ejemplo.
  getHistorialEquipo: (idMaquina: number, clase: string) =>
    httpClient.get<HistorialEquipo>(`${BASE}/equipos/${idMaquina}/${clase}/historial`),
};
