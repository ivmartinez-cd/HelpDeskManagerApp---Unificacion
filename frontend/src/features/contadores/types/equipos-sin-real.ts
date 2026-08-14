/** Nombres tal como los serializa el backend real (`EquipoSinRealSchema` en
 * `equipos_sin_real_schemas.py`, snake_case sin alias) — verificado contra el
 * endpoint vivo antes de cablear la tabla. */

export type SeveridadSinReal = "critico" | "alto" | "medio" | "bajo";

export interface EquipoSinReal {
  /** ID de Maquina en Siges — identidad estable de la fila (la serie puede
   * venir duplicada/sucia del legacy). */
  id_maquina: number;
  serie: string;
  modelo: string;
  tecnologia: string | null;
  propiedad: string | null;
  cliente: string;
  sucursal: string;
  estado_maquina: string;
  observaciones: string;
  /** null = nunca tuvo una toma real; `fecha_referencia` es la instalación. */
  fecha_ultimo_real: string | null;
  fecha_referencia: string;
  dias_sin_real: number;
  meses_sin_real: number;
  nunca_tuvo_real: boolean;
  im1: number;
  im2: number;
  im3: number;
  imp_prom_3m: number;
  severidad: SeveridadSinReal;
  /** Operador de facturación asignado al cliente (calendario de Gestión
   * cruzado contra Siges); null cuando el cliente no cruza. */
  operador_nombre: string | null;
  operador_color: string | null;
}

export interface EquiposSinRealResumen {
  total: number;
  criticos: number;
  altos: number;
  medios: number;
  bajos: number;
  nunca_real: number;
  consultado_en: string;
}

export type EquiposSinRealSortKey = "meses" | "cliente" | "sucursal" | "modelo" | "operador";

export interface EquiposSinRealListParams {
  page: number;
  size: number;
  sortBy: EquiposSinRealSortKey;
  sortDir: "asc" | "desc";
  minMeses: number;
  search?: string;
  refresh?: boolean;
}
