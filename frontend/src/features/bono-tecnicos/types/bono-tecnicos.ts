export interface PuntajeTecnico {
  tecnico: string;
  id_tecnico: number;
  periodo: number;
  correctivo: number;
  preventivo: number;
  inst_des: number;
  pre_correctivo: number;
  entrega_insumos: number;
  dias: number;
  /** Cuenta de solicitudes de TV en estado APROBADA del período — ya no es
   * carga manual (ver `SolicitudTv`). */
  tareas_varias: number;
  /** `null` mientras no se cargaron Días para este técnico y período. */
  puntaje: number | null;
  /** Sugerencia (días hábiles del período menos ausencias) desde Gestión de
   * Personal — `null` si el técnico no está vinculado a un empleado ahí
   * (ver "Vincular con Siges" en /vacaciones/gestion). No pisa `dias`
   * automáticamente: es una sugerencia editable, no un reemplazo. */
  dias_sugeridos: number | null;
}

export interface GuardarBonoInputBody {
  tecnico: string;
  dias: number;
}

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

/** Carga de TV a nombre de un técnico desde el panel de supervisor —
 * nace ya APROBADA en el backend, no pasa por la cola de pendientes. */
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

/** Categoría cruda tal como la manda el backend (`Categoria` de la consulta
 * agrupada a Siges) — no traducir a mano en cada lugar, usar `CATEGORIAS`. */
export type CategoriaIncidente =
  | "Correctivo"
  | "Preventivo"
  | "InstDes"
  | "PreCorrectivo"
  | "EntregaInsumos";

export interface IncidenteBono {
  id_incidente: number;
  categoria: CategoriaIncidente;
  cliente: string;
  sucursal: string;
  nro_serie: string;
}

/** Orden y etiqueta de cada categoría — mismo orden que el `ORDER BY` de
 * `incidentes_query.py` en el backend (Correctivo, Preventivo, Inst-Des,
 * Pre-Correctivo, Entrega Insumos). */
export const CATEGORIAS: { key: CategoriaIncidente; label: string }[] = [
  { key: "Correctivo", label: "Correctivo" },
  { key: "Preventivo", label: "Preventivo" },
  { key: "InstDes", label: "Inst-Des" },
  { key: "PreCorrectivo", label: "Pre-Correctivo" },
  { key: "EntregaInsumos", label: "Entrega de Insumos" },
];
