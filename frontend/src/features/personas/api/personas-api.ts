import { httpClient } from "@/services/http-client";

/** Tipos wire de `/api/personas` (ADR-040): camelCase por `serialization_alias`
 * en `persona_schemas.py`. El `id` es el de la ficha de empleado. */
export interface AccesoPersona {
  userId: string;
  activo: boolean;
  superadmin: boolean;
  ultimoIngreso: string | null;
}

export interface Persona {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  color: string;
  activa: boolean;
  sectorId: string;
  sectorNombre: string;
  cargoNombre: string;
  entraALaApp: boolean;
  acceso: AccesoPersona | null;
}

export interface DatosPersona {
  firstName: string;
  lastName: string;
  email: string;
  color: string;
}

interface PagePersonas {
  items: Persona[];
  total: number;
}

/** Catálogo chico (decenas de personas): la pantalla trae todo en una página y
 * filtra/ordena en el navegador, como hacía la pestaña Empleados. */
export const MAX_PERSONAS = 200;

const BASE = "/api/personas";

export const personasApi = {
  listTodas: () => httpClient.get<PagePersonas>(`${BASE}?size=${MAX_PERSONAS}`),
  get: (id: string) => httpClient.get<Persona>(`${BASE}/${id}`),
  updateDatos: (id: string, datos: DatosPersona) =>
    httpClient.patch<Persona>(`${BASE}/${id}/datos`, datos),
  darAcceso: (id: string) => httpClient.post<Persona>(`${BASE}/${id}/acceso`),
  quitarAcceso: (id: string) => httpClient.delete<Persona>(`${BASE}/${id}/acceso`),
};

export function nombrePersona(p: Pick<Persona, "firstName" | "lastName">): string {
  return `${p.firstName} ${p.lastName}`;
}
