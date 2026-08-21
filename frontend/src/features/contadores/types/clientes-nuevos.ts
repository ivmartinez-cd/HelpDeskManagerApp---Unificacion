/** Nombres tal como los serializa el backend (`clientes_nuevos_schemas.py`,
 * snake_case sin alias) — verificar contra el endpoint vivo antes de tocar. */

export type EstadoClienteNuevo =
  | "ESPERANDO_INSTALACION"
  | "STC_PENDIENTE"
  | "STC_ENVIADO"
  | "CERRADO";

/** Lo que Siges sabe de la empresa cruzada (anotado en lectura, puede faltar
 * si la ficha no está cruzada o Siges no respondió). `equipos_instalados` =
 * máquinas con "Alta en Cliente" (registro de instalas real). */
export interface ResumenSigesClienteNuevo {
  empresa_id: number;
  equipos_instalados: number;
  instalas: number;
  primera_instalacion: string | null;
  ultima_instalacion: string | null;
  equipos_con_toma: number;
  contrato_nro: string | null;
  fecha_firma: string | null;
  vendedor: string | null;
  rubro: string;
}

export interface ClienteNuevo {
  id: string;
  cliente: string;
  siges_empresa_id: number | null;
  contrato_nro: string | null;
  fecha_firma: string | null;
  vendedor: string | null;
  operador_id: string | null;
  implementacion_servicio: string | null;
  fecha_estimada_implementacion: string | null;
  fecha_estimada_primera_facturacion: string | null;
  dia_corte: number | null;
  equipos_previstos: number | null;
  estado: EstadoClienteNuevo;
  stc_enviado_el: string | null;
  notas: string | null;
  created_at: string;
  updated_at: string;
  siges: ResumenSigesClienteNuevo | null;
  /** Aviso del backend: sigue esperando instalación pero Siges ya muestra
   * los equipos instalados — hay que armar el STC. */
  listo_para_stc: boolean;
}

/** `ClienteNuevoIn` del backend — mismo body para alta y edición. */
export interface ClienteNuevoPayload {
  cliente: string;
  siges_empresa_id: number | null;
  contrato_nro: string | null;
  fecha_firma: string | null;
  vendedor: string | null;
  operador_id: string | null;
  implementacion_servicio: string | null;
  fecha_estimada_implementacion: string | null;
  fecha_estimada_primera_facturacion: string | null;
  dia_corte: number | null;
  equipos_previstos: number | null;
  estado: EstadoClienteNuevo;
  stc_enviado_el: string | null;
  notas: string | null;
}

export interface CandidatoClienteNuevo {
  empresa_id: number;
  cliente: string;
  contrato_nro: string | null;
  fecha_firma: string | null;
  vendedor: string | null;
  rubro: string;
  equipos_instalados: number;
}

export interface CandidatosClientesNuevos {
  candidatos: CandidatoClienteNuevo[];
  firmado_desde: string;
}
