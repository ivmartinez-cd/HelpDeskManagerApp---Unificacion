import type { DetalleContadorRow } from "../types/detalle-contador-proceso";

// Mismo criterio que `features/sla/lib/formato-whatsapp.ts`: agrupado —
// acá por sucursal, no por agente — con anclas en negrita y emoji de estado
// en vez de color (WhatsApp no soporta texto de color). La fecha se arma
// con split en vez de `new Date(iso)` porque el string es date-only
// ("YYYY-MM-DD") y `new Date()` lo interpreta en UTC, corriendo un día para
// un usuario en GMT-3 — mismo motivo que `formatFecha` de
// `detalle-contador-tabla.tsx`.

function formatFecha(iso: string | null): string {
  if (!iso) return "—";
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}

function formatNumero(n: number): string {
  return n.toLocaleString("es-AR");
}

function formatearFila(fila: DetalleContadorRow): string {
  const marca = fila.falta_contador ? "🔴" : "🟢";
  return (
    `${marca} *${fila.modelo}* — Serie ${fila.serie}${fila.sector ? ` · ${fila.sector}` : ""}\n` +
    `📅 Ant. ${formatFecha(fila.fecha_toma_anterior)} (${formatNumero(fila.contador_anterior)}) → ` +
    `Act. ${formatFecha(fila.fecha_toma_actual)} (${formatNumero(fila.contador_actual)})\n` +
    `🖨️ Impr: ${formatNumero(fila.impresiones_reales)} · ${fila.tipo ?? "—"} · ${fila.estado_maquina ?? "—"}`
  );
}

function agruparPorSucursal(filas: DetalleContadorRow[]): [string, DetalleContadorRow[]][] {
  const grupos = new Map<string, DetalleContadorRow[]>();
  for (const fila of filas) {
    const lista = grupos.get(fila.sucursal) ?? [];
    lista.push(fila);
    grupos.set(fila.sucursal, lista);
  }
  // Alfabético: a diferencia de SLA (agente más cargado primero, urgencia),
  // acá es un listado para que el cliente ubique su sucursal.
  return [...grupos.entries()].sort((a, b) => a[0].localeCompare(b[0], "es"));
}

export function formatearTablaWhatsapp(
  filas: DetalleContadorRow[],
  cliente: string,
  alcanceLabel: string,
): string {
  const bloques = agruparPorSucursal(filas).map(([sucursal, filasGrupo]) =>
    [
      `📍 *${sucursal}* (${filasGrupo.length})`,
      "",
      filasGrupo.map(formatearFila).join("\n\n"),
    ].join("\n"),
  );

  return [
    `📋 *Detalle de contadores — ${cliente}*`,
    `${alcanceLabel} · ${filas.length} equipos`,
    "",
    bloques.join("\n\n\n"),
  ].join("\n");
}
