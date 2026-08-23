/** Wire types del backend `preventivos` — snake_case tal cual serializan los
 * schemas (`preventivos_schemas.py`, sin `serialization_alias`). Verificado
 * contra respuestas reales del endpoint el 2026-08-14. */

export type EstadoPreventivo =
  | "vencido"
  | "por_vencer"
  | "al_dia"
  | "sin_preventivo"
  | "sin_frecuencia";

export interface HabilitacionPreventivo {
  habilitado_por: string;
  habilitado_en: string;
  nota: string | null;
}

export interface EquipoPreventivo {
  id_maquina: number;
  serie: string;
  modelo: string;
  cliente: string;
  sucursal: string;
  zona: string;
  frecuencia_dias: number | null;
  fecha_ultimo_preventivo: string | null;
  proximo_vencimiento: string | null;
  estado: EstadoPreventivo;
  dias_vencido: number | null;
  habilitacion: HabilitacionPreventivo | null;
}

export interface ZonaParque {
  zona: string;
  maquinas_activas: number;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

/** `Page` + sello de frescura de la caché del backend (TTL 5 min). */
export interface EquiposPreventivosPage extends Page<EquipoPreventivo> {
  consultado_en: string;
}

export interface ListEquiposParams {
  zona: string;
  estado?: EstadoPreventivo;
  habilitado?: boolean;
  q?: string;
  page?: number;
  size?: number;
  refresh?: boolean;
}

/** Una sucursal (no una máquina) para el mapa: `peor_estado` es el más
 * urgente de su parque, mismo criterio que el orden de la tabla. */
export interface PuntoMapaPreventivo {
  id_sucursal: number;
  cliente: string;
  sucursal: string;
  zona: string;
  domicilio: string;
  latitud: number | null;
  longitud: number | null;
  ubicado: boolean;
  cant_maquinas: number;
  cant_habilitadas: number;
  peor_estado: EstadoPreventivo;
  dias_vencido_max: number | null;
}

/** `Page` + sello de frescura + cuántas sucursales del filtro actual no
 * tienen coordenada usable (se avisa, no se esconde). */
export interface PuntosMapaPage extends Page<PuntoMapaPreventivo> {
  consultado_en: string;
  sin_ubicar: number;
}

export interface ListPuntosMapaParams {
  zona: string;
  estado?: EstadoPreventivo;
  habilitado?: boolean;
  q?: string;
  refresh?: boolean;
}

/** Resultado de disparar la geocodificación (universo completo, no solo la
 * zona actual — ver domain/entities/sucursal_coordenadas.py). */
export interface GeocodificarResultado {
  resueltas: number;
  ambiguas: number;
  sin_resultados: number;
  sin_direccion: number;
}
