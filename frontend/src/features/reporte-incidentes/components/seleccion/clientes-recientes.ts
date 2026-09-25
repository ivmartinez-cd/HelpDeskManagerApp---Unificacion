/** Últimos clientes elegidos, en localStorage (conveniencia por navegador:
 * si el storage no está disponible, simplemente no hay recientes). */

import type { Empresa } from "../../types/reporte";

const CLAVE = "reporte-incidentes:clientes-recientes";
const MAX_RECIENTES = 5;

export function leerRecientes(): Empresa[] {
  try {
    const crudo = localStorage.getItem(CLAVE);
    const lista: unknown = crudo ? JSON.parse(crudo) : [];
    return Array.isArray(lista)
      ? lista.filter((e): e is Empresa => typeof e?.id === "string" && typeof e?.nombre === "string")
      : [];
  } catch {
    return []; // storage bloqueado o JSON corrupto: sin recientes
  }
}

export function guardarReciente(empresa: Empresa, actuales: Empresa[]): Empresa[] {
  const siguientes = [
    { id: empresa.id, nombre: empresa.nombre },
    ...actuales.filter((e) => e.id !== empresa.id),
  ].slice(0, MAX_RECIENTES);
  try {
    localStorage.setItem(CLAVE, JSON.stringify(siguientes));
  } catch {
    // sin persistencia: la selección sigue igual
  }
  return siguientes;
}
