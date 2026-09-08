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
  /** Cuenta de solicitudes de TV en estado APROBADA del período — se cargan
   * y aprueban desde el módulo `tareas-varias`, de solo lectura acá. */
  tareas_varias: number;
  /** `null` mientras no se cargaron Días para este técnico y período. */
  puntaje: number | null;
  /** Sugerencia (días hábiles del período menos ausencias) desde Gestión de
   * Personal — `null` si el técnico no está vinculado a un empleado ahí
   * (ver "Vincular con Siges" en /vacaciones/gestion). No pisa `dias`
   * automáticamente: es una sugerencia editable, no un reemplazo. */
  dias_sugeridos: number | null;
}

/** Resumen del bono del técnico autenticado (`GET /mi-resumen`) — mismos
 * campos que `PuntajeTecnico` sin `tareas_varias` (reemplazado por el
 * desglose de TV por estado, que sí puede ver este endpoint aunque el
 * técnico no tenga `bono-tecnicos.view`). Las solicitudes de TV en sí son
 * del módulo `tareas-varias`, ver `features/tareas-varias/types`. */
export interface MiResumenBono {
  tecnico: string;
  id_tecnico: number;
  periodo: number;
  correctivo: number;
  preventivo: number;
  inst_des: number;
  pre_correctivo: number;
  entrega_insumos: number;
  dias: number;
  puntaje: number | null;
  dias_sugeridos: number | null;
  tv_aprobadas: number;
  tv_pendientes: number;
  tv_rechazadas: number;
}

export interface GuardarBonoInputBody {
  tecnico: string;
  dias: number;
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

/** Un mes de la evolución anual (vista de gerencia). `puntaje` es `null`
 * cuando ese mes no tenía Días cargados — hueco en el gráfico, no un 0. */
export interface PuntoMensual {
  periodo: number;
  puntaje: number | null;
  incidentes: number;
  dias: number;
  tv_solicitadas: number;
  tv_aprobadas: number;
}

export interface EvolucionTecnico {
  tecnico: string;
  id_tecnico: number;
  puntos: PuntoMensual[];
  puntaje_promedio: number | null;
  incidentes_total: number;
  tv_solicitadas_total: number;
  tv_aprobadas_total: number;
}

export interface EvolucionEquipo {
  anio: number;
  puntos: PuntoMensual[];
}
