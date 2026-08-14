export interface Contacto {
  id: string;
  prestadorId: string;
  nombre: string;
  telefono: string | null;
  email: string | null;
  isPrincipal: boolean;
  sortOrder: number;
}

export interface Prestador {
  id: string;
  sigesEmpresaId: number;
  denComercial: string;
  razonSocial: string | null;
  cuit: string | null;
  equipos: number | null;
  operadorId: string | null;
  operadorNombre: string | null;
  operadorColor: string | null;
  isActive: boolean;
  contactos: Contacto[];
}

export interface OperadorGroup {
  operadorId: string | null;
  operadorNombre: string | null;
  operadorColor: string | null;
  prestadores: Prestador[];
}

export interface PrestadoresResumen {
  totalPrestadores: number;
  totalActivos: number;
  operadoresConPst: number;
  sinAsignar: number;
  grupos: OperadorGroup[];
}

export interface OperadorOption {
  id: string;
  fullName: string;
  color: string | null;
}

export interface AsignacionHistorial {
  id: string;
  operadorId: string | null;
  operadorNombre: string | null;
  desde: string;
  hasta: string | null;
}

export interface SyncResult {
  actualizados: string[];
  sinCambios: number;
}

export interface CreatePrestadorPayload {
  sigesEmpresaId: number;
  denComercial: string;
  razonSocial?: string | null;
  cuit?: string | null;
  operadorId?: string | null;
}

export interface UpdatePrestadorPayload {
  denComercial: string;
  razonSocial?: string | null;
  cuit?: string | null;
}

export interface UpsertContactoPayload {
  nombre: string;
  telefono?: string | null;
  email?: string | null;
  isPrincipal?: boolean;
  sortOrder?: number;
}
