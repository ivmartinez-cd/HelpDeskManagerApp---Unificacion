export interface PrestadorLiquidacion {
  id: string;
  nombre: string;
  nombreCorto: string;
  cuit: string | null;
  region: string | null;
  activo: boolean;
  sigesEmpresaId: number | null;
  cdPrestadorId: number | null;
  sigesBaseSucursalId: number | null;
  createdAt: string;
  updatedAt: string;
}

export interface SucursalPropia {
  sigesSucursalId: number;
  descripcion: string;
  latitud: string | null;
  longitud: string | null;
  tieneCoords: boolean;
}

export interface Spst {
  id: string;
  prestadorId: string;
  nombre: string;
  domicilio: string | null;
  localidad: string | null;
  provincia: string | null;
  zonaCobertura: string | null;
  activo: boolean;
  sigesEmpresaId: number | null;
  sigesBaseSucursalId: number | null;
  createdAt: string;
}
