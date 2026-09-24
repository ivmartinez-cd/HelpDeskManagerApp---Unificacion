/** Contrato de `/api/insumos/despachados/*` tal como lo serializa el backend
 * (`presentation/schemas/despachados_schemas.py` y
 * `despachados_detalle_schemas.py`): camelCase por `alias_generator`, fechas
 * `date` como `YYYY-MM-DD` y `datetime` como ISO con zona. */

/** `ColorSemaforo` del dominio. */
export type ColorSemaforo = "verde" | "amarillo" | "naranja" | "rojo" | "gris" | "cerrado";

export type TipoAccion = "llamado_cliente" | "mail_cliente" | "reclamo_oca" | "otro";

export type ResultadoAccion = "resuelto" | "pendiente" | "sin_respuesta";

export type OrigenCorrida = "programada" | "manual";

export interface UltimaAccionDespacho {
  tipo: TipoAccion;
  resultado: ResultadoAccion;
  usuarioNombre: string;
  creadaEn: string;
}

/** Fila de la tabla "Todos los despachos" (`FilaDespachoOut`). */
export interface FilaDespacho {
  guia: string;
  color: ColorSemaforo;
  alertaAbierta: boolean;
  observacion: string;
  fechaLimite: string | null;
  /** Solo en rojo con fecha límite: 0 vence hoy, negativo vencido. */
  diasHabilesParaLimite: number | null;
  estado: string;
  motivo: string;
  sucursalOca: string;
  fechaEstado: string | null;
  operativa: string;
  cliente: string;
  fechaRemito: string;
  numeroRemito: number | null;
  cantidadRemitos: number;
  incidente: string;
  cantidadIncidentes: number;
  ultimaAccion: UltimaAccionDespacho | null;
  conError: boolean;
}

/** Tarjetas, contadores del menú y opciones de operativa (`ResumenOut`). */
export interface ResumenDespachos {
  /** Todas las claves de `ColorSemaforo` vienen presentes. */
  porColor: Record<ColorSemaforo, number>;
  alertasRojas: number;
  alertasNaranjas: number;
  naranjasSinAccion: number;
  limiteMasProximo: string | null;
  diasHabilesLimiteMasProximo: number | null;
  operativas: string[];
}

export interface CorridaDespachos {
  id: number;
  origen: OrigenCorrida;
  usuarioNombre: string | null;
  iniciadaEn: string;
  terminadaEn: string | null;
  enviosNuevos: number;
  consultasOk: number;
  consultasError: number;
  error: string | null;
}

export interface EstadoActualizacionDespachos {
  enCurso: boolean;
  /** Cuándo arrancó la corrida en curso; null si no hay ninguna. */
  iniciadaEn: string | null;
  ultimaTerminada: CorridaDespachos | null;
}

export interface ActualizacionLanzada {
  enCurso: boolean;
}

/** Body de `POST /despachados/{guia}/acciones` (`AccionIn`). */
export interface NuevaAccionDespacho {
  tipo: TipoAccion;
  detalle: string;
  resultado: ResultadoAccion;
  cerrarAlerta: boolean;
}

export interface AccionDespacho {
  id: number;
  guia: string;
  tipo: TipoAccion;
  detalle: string;
  resultado: ResultadoAccion;
  cerroAlerta: boolean;
  usuarioNombre: string;
  creadaEn: string;
}

export interface EstadoOcaDespacho {
  operativa: string;
  ordenRetiro: string;
  sucursalActual: string;
  fechaEstado: string;
  estado: string;
  idEstado: number | null;
  motivo: string;
  cantidadPaquetes: number | null;
}

export interface EnvioDespacho {
  guia: string;
  idDistribucion: number;
  fechaRemito: string;
  cliente: string;
  sucursalCliente: string;
  color: ColorSemaforo;
  /** Las reglas piden acción (rojo o naranja), esté o no cerrada la alerta. */
  alerta: boolean;
  alertaAbierta: boolean;
  abierto: boolean;
  fechaLimite: string | null;
  observacion: string;
  estadoOca: EstadoOcaDespacho | null;
  consultadoEn: string | null;
  ultimoError: { mensaje: string; ocurridoEn: string } | null;
  cierreAlerta: { cerradaEn: string; usuarioNombre: string } | null;
}

export interface IncidenteDespacho {
  numero: string;
  numeroCliente: string;
}

export interface RemitoDespacho {
  idRemito: number;
  numeroRemito: number;
  fechaRemito: string;
  idDistribucion: number;
  bultos: number;
  cliente: string;
  sucursalCliente: string;
  entregaA: string;
  incidentes: IncidenteDespacho[];
}

export interface CambioEstadoDespacho {
  idEstado: number | null;
  estado: string;
  motivo: string;
  sucursal: string;
  fechaEstado: string;
  color: ColorSemaforo;
  observadoEn: string;
}

/** `GET /despachados/{guia}` (`DetalleOut`). */
export interface DetalleDespacho {
  envio: EnvioDespacho;
  diasHabilesParaLimite: number | null;
  /** Del más viejo al más nuevo. */
  remitos: RemitoDespacho[];
  /** Del más reciente al más viejo. */
  cambios: CambioEstadoDespacho[];
  /** De la más reciente a la más vieja. */
  acciones: AccionDespacho[];
}

/** Columna por la que se ordena la tabla (`orden` del listado). `urgencia` es
 * el orden por defecto (rojos primero, con sus desempates) e ignora la dirección. */
export type ColumnaOrdenDespachos =
  | "urgencia"
  | "color"
  | "guia"
  | "remito"
  | "cliente"
  | "incidente"
  | "estado"
  | "sucursal"
  | "fecha_remito"
  | "fecha_estado"
  | "limite";

/** Filtros y orden de la tabla "Todos los despachos" (query string del listado). */
export interface FiltrosDespachos {
  texto: string;
  /** Uno o más colores separados por coma (`"verde,amarillo"`); vacío = todos. */
  colores: string;
  operativa: string;
  remitoDesde: string | null;
  remitoHasta: string | null;
  orden: ColumnaOrdenDespachos;
  direccion: "asc" | "desc";
}

/** Contacto de la cuenta de Canal Directo en OCA (según el prefijo de la guía). */
export interface ContactoReclamoOca {
  nombre: string;
  apellido: string;
  empresa: string;
  email: string;
  /** Solo dígitos. */
  cuit: string;
  /** "" si la cuenta no tiene uno cargado. */
  telefono: string;
}

/** `GET /despachados/{guia}/reclamo-oca`: datos para precargar el formulario
 * público de reclamos de OCA. */
export interface ReclamoOca {
  guia: string;
  /** La última que informó OCA; "" si todavía no registra la guía. */
  operativa: string;
  /** null si ninguna regla reconoce el prefijo de la guía. */
  contacto: ContactoReclamoOca | null;
  comentario: string;
}
