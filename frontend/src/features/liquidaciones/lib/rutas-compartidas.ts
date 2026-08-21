import type { Incidente } from "../types/liquidaciones";

/** Ids de incidentes que posiblemente comparten ruta con otro del mismo día
 * (misma localidad o mismo destino) — extraído de `incidentes-tabla.tsx`
 * porque ese archivo ya superaba el tamaño máximo de archivo (§4). */
export function computeRutasCompartidas(incidentes: Incidente[]): Set<string> {
  const ids = new Set<string>();
  const byFecha = new Map<string, Incidente[]>();
  for (const inc of incidentes) {
    if (!inc.fechaCierre || (inc.cantKmCobrado ?? 0) <= 0) continue;
    const list = byFecha.get(inc.fechaCierre) ?? [];
    list.push(inc);
    byFecha.set(inc.fechaCierre, list);
  }
  for (const incsDay of byFecha.values()) {
    if (incsDay.length < 2) continue;
    for (const inc of incsDay) {
      for (const otro of incsDay) {
        if (otro.id === inc.id) continue;
        const mismaLocalidad =
          inc.localidadCliente &&
          otro.localidadCliente &&
          inc.localidadCliente.trim().toLowerCase() ===
            otro.localidadCliente.trim().toLowerCase();
        const mismaDestino =
          inc.empresaNombre &&
          otro.empresaNombre &&
          inc.empresaNombre.trim().toLowerCase() ===
            otro.empresaNombre.trim().toLowerCase() &&
          inc.sucursalNombre &&
          otro.sucursalNombre &&
          inc.sucursalNombre.trim().toLowerCase() ===
            otro.sucursalNombre.trim().toLowerCase();
        if (mismaLocalidad || mismaDestino) ids.add(inc.id);
      }
    }
  }
  return ids;
}
