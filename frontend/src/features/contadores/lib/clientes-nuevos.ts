import type {
  CandidatoClienteNuevo,
  ClienteNuevo,
  ClienteNuevoPayload,
  EstadoClienteNuevo,
} from "../types/clientes-nuevos";

type BadgeVariant = "neutral" | "accent" | "success" | "warning" | "danger";

/** Ciclo que sigue la TL (ver `cliente_nuevo.py`): esperando que el PST
 * instale → equipos instalados, STC por armar/enviar → STC enviado, a la
 * espera de la 1ª facturación → cerrada. */
export const ESTADO_META: Record<EstadoClienteNuevo, { label: string; variant: BadgeVariant }> =
  {
    ESPERANDO_INSTALACION: { label: "Esperando instalación", variant: "neutral" },
    STC_PENDIENTE: { label: "STC pendiente", variant: "warning" },
    STC_ENVIADO: { label: "STC enviado", variant: "success" },
    CERRADO: { label: "Cerrada", variant: "neutral" },
  };

export const ESTADOS: EstadoClienteNuevo[] = [
  "ESPERANDO_INSTALACION",
  "STC_PENDIENTE",
  "STC_ENVIADO",
  "CERRADO",
];

export type FiltroEstado = "abiertas" | "todas" | EstadoClienteNuevo;

export const FILTROS_ESTADO: { value: FiltroEstado; label: string }[] = [
  { value: "abiertas", label: "Abiertas" },
  { value: "ESPERANDO_INSTALACION", label: "Esperando instalación" },
  { value: "STC_PENDIENTE", label: "STC pendiente" },
  { value: "STC_ENVIADO", label: "STC enviado" },
  { value: "CERRADO", label: "Cerradas" },
  { value: "todas", label: "Todas" },
];

export const RUBRO_LABEL: Record<string, string> = {
  IMPRESION: "Impresión",
  CARTELERIA: "Cartelería",
  IT: "IT",
  OTRO: "Otro",
  DESCONOCIDO: "Sin rubro",
};

export function cumpleFiltro(ficha: ClienteNuevo, filtro: FiltroEstado): boolean {
  if (filtro === "todas") return true;
  if (filtro === "abiertas") return ficha.estado !== "CERRADO";
  return ficha.estado === filtro;
}

export function coincideBusqueda(ficha: ClienteNuevo, q: string): boolean {
  if (!q) return true;
  const campos = [
    ficha.cliente,
    ficha.contrato_nro,
    ficha.vendedor,
    ficha.operador_id,
    ficha.notas,
    ficha.siges?.contrato_nro,
    ficha.siges?.vendedor,
  ];
  return campos.some((c) => c?.toLowerCase().includes(q));
}

/** "2026-08-06" → "06/08/2026"; null/"" → "—". */
export function formatFecha(iso: string | null | undefined): string {
  if (!iso) return "—";
  const [y, m, d] = iso.slice(0, 10).split("-");
  return `${d}/${m}/${y}`;
}

export function hoyIso(): string {
  const d = new Date();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
}

export const PAYLOAD_VACIO: ClienteNuevoPayload = {
  cliente: "",
  siges_empresa_id: null,
  contrato_nro: null,
  fecha_firma: null,
  vendedor: null,
  operador_id: null,
  implementacion_servicio: null,
  fecha_estimada_implementacion: null,
  fecha_estimada_primera_facturacion: null,
  dia_corte: null,
  equipos_previstos: null,
  estado: "ESPERANDO_INSTALACION",
  stc_enviado_el: null,
  notas: null,
};

export function payloadDesdeFicha(f: ClienteNuevo): ClienteNuevoPayload {
  return {
    cliente: f.cliente,
    siges_empresa_id: f.siges_empresa_id,
    contrato_nro: f.contrato_nro,
    fecha_firma: f.fecha_firma,
    vendedor: f.vendedor,
    operador_id: f.operador_id,
    implementacion_servicio: f.implementacion_servicio,
    fecha_estimada_implementacion: f.fecha_estimada_implementacion,
    fecha_estimada_primera_facturacion: f.fecha_estimada_primera_facturacion,
    dia_corte: f.dia_corte,
    equipos_previstos: f.equipos_previstos,
    estado: f.estado,
    stc_enviado_el: f.stc_enviado_el,
    notas: f.notas,
  };
}

/** Precarga desde una sugerencia de Siges: lo que el mail de Comercial
 * repite (cliente, contrato, firma, vendedor) ya viene cargado. "Equipos
 * previstos" NO se precarga con lo instalado: es la cantidad comprometida
 * (viene del mail) y tiene que ser independiente de lo que Siges ya muestra,
 * si no "Listo para STC" se enciende solo. */
export function payloadDesdeCandidato(c: CandidatoClienteNuevo): ClienteNuevoPayload {
  return {
    ...PAYLOAD_VACIO,
    cliente: c.cliente,
    siges_empresa_id: c.empresa_id,
    contrato_nro: c.contrato_nro,
    fecha_firma: c.fecha_firma,
    vendedor: c.vendedor,
  };
}

/** Texto de avance de instalación: "11 / 10 · últ. 21/08/2026" o "—". */
export function textoInstalados(f: ClienteNuevo): string {
  if (!f.siges) return f.siges_empresa_id ? "Siges sin respuesta" : "Sin cruce";
  const previstos = f.equipos_previstos ? ` / ${f.equipos_previstos}` : "";
  const ultima = f.siges.ultima_instalacion
    ? ` · últ. ${formatFecha(f.siges.ultima_instalacion)}`
    : "";
  return `${f.siges.equipos_instalados}${previstos}${ultima}`;
}
