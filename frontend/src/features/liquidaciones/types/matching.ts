/** Matching de sucursales Tabla KM ↔ Siges (Fase 1): N1 auto-vinculable
 * (símbolo/abreviatura) y N2 con candidatos difusos que siempre requieren
 * confirmación humana. */
export interface VinculoN1Aplicado {
  tablaKmId: string;
  empresaNombre: string;
  sucursalNombre: string;
  sigesSucursalId: number;
}

export interface ResultadoAutoVinculoN1 {
  vinculadas: number;
  sinCambios: number;
  detalle: VinculoN1Aplicado[];
}

export interface CandidatoN2Match {
  sigesSucursalId: number;
  sucursalNombre: string;
  domicilio: string | null;
  score: number;
  motivo: string;
  /** Misma dirección normalizada que la fila local (sucursal renombrada). */
  mismaDireccion: boolean;
}

export interface PropuestaN2Match {
  tablaKmId: string;
  empresaNombre: string;
  sucursalNombre: string;
  candidatos: CandidatoN2Match[];
}
