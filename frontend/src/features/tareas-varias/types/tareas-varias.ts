export type EstadoSolicitudTv = "PENDIENTE" | "APROBADA" | "RECHAZADA";

export interface SolicitudTv {
  id: string;
  id_tecnico: number;
  tecnico: string;
  periodo: number;
  fecha: string;
  razon_social: string;
  sucursal: string;
  tarea_realizada: string;
  estado: EstadoSolicitudTv;
  creado_en: string;
  resuelta_en: string | null;
  resuelta_por_email: string | null;
  motivo_rechazo: string | null;
}

/** `id_tecnico`/`tecnico` no viajan: el backend los resuelve del vínculo
 * Empleado↔Siges del usuario autenticado. */
export interface CrearSolicitudTvBody {
  fecha: string;
  razon_social: string;
  sucursal: string;
  tarea_realizada: string;
}

/** Carga de TV a nombre de un técnico desde el panel de supervisor — nace ya
 * APROBADA en el backend, no pasa por la cola de pendientes. `id_tecnico`
 * viaja en la URL (`POST /a-nombre-de/{id_tecnico}`) y `tecnico` en el body,
 * los dos escritos a mano por quien carga (no hay catálogo de técnicos
 * propio de este módulo, ver Bono Técnicos para el ID de cada uno). */
export interface CrearSolicitudTvAdminBody {
  tecnico: string;
  fecha: string;
  razon_social: string;
  sucursal: string;
  tarea_realizada: string;
}

export interface DecisionSolicitudTvBody {
  decision: Extract<EstadoSolicitudTv, "APROBADA" | "RECHAZADA">;
  motivo?: string;
}
