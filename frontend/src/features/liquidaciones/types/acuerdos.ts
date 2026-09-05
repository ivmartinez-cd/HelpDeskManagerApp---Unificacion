/** Acuerdo de precio por cliente dentro de un prestador: el motor toma el
 * precio acordado (factor sobre el tarifario, o monto fijo) como el esperado
 * de ALT001, así la TL no resuelve cada mes las mismas alertas con el mismo
 * motivo (caso SALTA: mineras al doble, Refinor y YAGUAR con precio propio). */
export interface AcuerdoPrecioCliente {
  id: string;
  prestadorId: string;
  empresaNombre: string;
  /** null = todos los tipos de servicio. */
  tipoServicio: string | null;
  /** Multiplicador del tarifario (2 = precio doble). Excluyente con precioFijo. */
  factor: number | null;
  precioFijo: number | null;
  motivo: string;
  vigenciaDesde: string;
  vigenciaHasta: string | null;
  createdAt: string;
}

export interface AcuerdoBody {
  prestadorId: string;
  empresaNombre: string;
  tipoServicio?: string;
  factor?: number;
  precioFijo?: number;
  motivo: string;
  vigenciaDesde: string;
  vigenciaHasta?: string;
}
