import { httpClient } from "@/services/http-client";
import type {
  AccionDespacho,
  ActualizacionLanzada,
  DetalleDespacho,
  EnvioDespacho,
  EstadoActualizacionDespachos,
  FilaDespacho,
  FiltrosDespachos,
  NuevaAccionDespacho,
  ResumenDespachos,
} from "../types/despachados";
import { BASE, toQuery, type Page } from "./insumos-api-base";

const DESPACHADOS = `${BASE}/despachados`;

/** Métodos de `/api/insumos/despachados/*` (Insumos > Despachados). Todas las
 * lecturas salen de la base de HDM: ninguna espera a OCA. "Actualizar ahora"
 * responde 202 y la pantalla sigue el avance con `getActualizacion`. */
export const despachadosApi = {
  /** Tabla "Todos los despachos": filtrada y paginada en SQL, rojos primero. */
  listar: (filtros: FiltrosDespachos, page: number, size: number) =>
    httpClient.get<Page<FilaDespacho>>(
      `${DESPACHADOS}${toQuery({
        texto: filtros.texto || undefined,
        colores: filtros.colores || undefined,
        operativa: filtros.operativa || undefined,
        remitoDesde: filtros.remitoDesde,
        remitoHasta: filtros.remitoHasta,
        page,
        size,
      })}`,
    ),

  /** Tarjetas por color, contadores de alertas y opciones de operativa. */
  getResumen: () => httpClient.get<ResumenDespachos>(`${DESPACHADOS}/resumen`),

  /** Si hay una corrida en curso y el resumen de la última terminada. */
  getActualizacion: () =>
    httpClient.get<EstadoActualizacionDespachos>(`${DESPACHADOS}/actualizacion`),

  /** "Actualizar ahora": 202 enseguida; 409 si ya hay una corrida en curso. */
  actualizar: () => httpClient.post<ActualizacionLanzada>(`${DESPACHADOS}/actualizar`),

  /** Detalle de una guía para el panel lateral. */
  getDetalle: (guia: string) =>
    httpClient.get<DetalleDespacho>(`${DESPACHADOS}/${encodeURIComponent(guia)}`),

  /** Registra una acción del operador (opcionalmente cerrando la alerta). */
  registrarAccion: (guia: string, body: NuevaAccionDespacho) =>
    httpClient.post<AccionDespacho>(
      `${DESPACHADOS}/${encodeURIComponent(guia)}/acciones`,
      body,
    ),

  /** Da la alerta por atendida (exige al menos una acción registrada). */
  cerrarAlerta: (guia: string) =>
    httpClient.post<EnvioDespacho>(`${DESPACHADOS}/${encodeURIComponent(guia)}/cerrar-alerta`),
};
