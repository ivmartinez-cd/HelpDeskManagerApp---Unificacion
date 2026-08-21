// ── Sync de tarifarios contra Siges (ADR-014 dataset 2) ────────────────────

export interface GrupoTarifasCreadas {
  prestador: string;
  tipoServicio: string;
  zona: string | null;
  cantidad: number;
}

export interface ConflictoTarifario {
  prestador: string;
  tipoServicio: string;
  zona: string | null;
  vigenciaDesde: string;
  campo: string;
  valorLocal: number;
  valorSiges: number;
}

export interface ZonaSinMapear {
  prestador: string;
  descripcionSiges: string;
  filas: number;
}

export interface SyncTarifariosResult {
  dryRun: boolean;
  creados: number;
  gruposCreados: GrupoTarifasCreadas[];
  conflictos: ConflictoTarifario[];
  sinCambios: number;
  zonasSinMapear: ZonaSinMapear[];
  prestadoresSinVinculo: string[];
}

export interface Tarifario {
  id: string;
  prestadorId: string;
  tipoServicio: string;
  zona: string | null;
  costoServicio: number;
  costoKm: number;
  vigenciaDesde: string;
  vigenciaHasta: string | null;
  createdAt: string;
}
