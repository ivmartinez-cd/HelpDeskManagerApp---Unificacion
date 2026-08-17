/** Nombres tal como los serializa el backend real (`AnexoPendienteSchema` en
 * `anexos_pendientes_schemas.py`, snake_case sin alias) — verificado contra
 * el endpoint vivo antes de cablear la tabla. */

export type EstadoAnexoPendiente = "en_proceso" | "demorado";

export interface AnexoPendiente {
  id_anexo: number;
  grupo: string | null;
  contrato: string | null;
  anexo: string;
  empresa_admin: string | null;
  vendedor: string | null;
  moneda: string | null;
  moneda_facturacion: string | null;
  /** Período de facturación abierto, formato YYYYMM. */
  periodo: string;
  fecha_proceso: string;
  estado: EstadoAnexoPendiente;
  /** Pydantic serializa `Decimal` como string JSON. */
  importe_usd: string;
  operador_nombre: string | null;
  operador_color: string | null;
}

export interface AnexosPendientesResumen {
  total: number;
  en_proceso: number;
  demorados: number;
  importe_usd_total: string;
  /** Período considerado EN PROCESO (el mes anterior al en curso). */
  periodo_referencia: string;
  consultado_en: string;
}

export interface AnexosPendientesListParams {
  estado?: EstadoAnexoPendiente;
  search?: string;
  refresh?: boolean;
}
