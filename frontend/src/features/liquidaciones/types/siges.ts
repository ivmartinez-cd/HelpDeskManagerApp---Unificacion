// ── Vínculo y sync contra Siges (ADR-014) ──────────────────────────────────

export interface SigesEmpresa {
  sigesEmpresaId: number;
  denComercial: string;
  razonSocial: string | null;
  cuit: string | null;
  tipo: "PST" | "SPST";
}

export interface PropuestaVinculo {
  entidad: "prestador" | "spst";
  localId: string;
  localNombre: string;
  sigesEmpresaId: number;
  sigesDenComercial: string;
}

export interface PropuestasVinculo {
  propuestas: PropuestaVinculo[];
  disponibles: SigesEmpresa[];
}

export interface SyncSigesCambio {
  localId: string;
  localNombre: string;
  campo: string;
  valorAnterior: string | null;
  valorNuevo: string | null;
}

export interface SyncSigesDiferenciaNombre {
  localId: string;
  localNombre: string;
  sigesDenComercial: string;
}

export interface SyncSigesResult {
  dryRun: boolean;
  cambios: SyncSigesCambio[];
  nombresDistintos: SyncSigesDiferenciaNombre[];
  sinCambios: number;
  sinVinculo: string[];
  vinculoRoto: string[];
}

export interface ZonaSigesEstado {
  prestadorId: string;
  prestador: string;
  descripcionSiges: string;
  /** true con zonaLocal null = mapeada a la zona genérica (sin zona). */
  mapeada: boolean;
  zonaLocal: string | null;
  propuesta: string | null;
  zonasLocales: string[];
}

export interface ZonasSiges {
  zonas: ZonaSigesEstado[];
}

export interface SucursalSiges {
  sigesSucursalId: number;
  empresaNombre: string;
  sucursalNombre: string;
  domicilio: string | null;
  localidad: string | null;
  provincia: string | null;
  yaCargada: boolean;
  actividadReciente: boolean;
}
