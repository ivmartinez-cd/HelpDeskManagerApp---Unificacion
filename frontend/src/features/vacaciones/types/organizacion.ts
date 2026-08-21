import type { UsuarioOption } from "./empleados";

export interface Sector {
  id: string;
  name: string;
  color: string;
  empleadosCount: number;
  jefes: UsuarioOption[];
}

export interface SectorPayload {
  name: string;
  color: string;
  jefeUserId: string | null;
}

export interface Cargo {
  id: string;
  name: string;
  maxSimultaneos: number | null;
  empleadosCount: number;
}

export interface CargoPayload {
  name: string;
  maxSimultaneos: number | null;
}
