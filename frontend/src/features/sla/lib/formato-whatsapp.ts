import type { IncidenteVencido } from "../types/sla";

// Se probó primero una tabla monospace (```...```) con columnas alineadas a
// padding — en el celular, el word-wrap de WhatsApp rompe la alineación cada
// vez que una fila no entra en el ancho de la burbuja, así que con 8+
// columnas todo terminaba truncado e ilegible. Después se pasó a texto
// corrido por incidente, pero sin línea en blanco entre incidentes quedaba
// un bloque pegado e ilegible (feedback real con captura de pantalla,
// 2026-09-09). Versión actual: agrupado por agente (con subtotal, igual
// criterio que "vencidos por técnico" del resumen), separado con líneas en
// blanco, y con anclas en negrita (agente, ID, horas vencidas) para escanear
// rápido. "Región" se sacó del todo por redundante: ya se sabe LOCAL vs
// INTERIOR mirando si `agente` es "Local" o el nombre de un operador.

function formatFecha(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("es-AR", {
    day: "2-digit",
    month: "2-digit",
  });
}

// WhatsApp no soporta color de texto — el emoji de color es lo más cercano.
// Umbrales sobre horas vencido (no sobre el SLA de cada uno, que varía de
// 24 a 96h): un corte único es más fácil de leer de un vistazo que uno
// proporcional al SLA de cada fila.
function semaforoVencido(horasVencido: number): string {
  if (horasVencido > 100) return "🔴";
  if (horasVencido > 24) return "🟠";
  return "🟡";
}

function formatearIncidente(row: IncidenteVencido): string {
  return (
    `${semaforoVencido(row.horas_vencido)} *#${row.id_incidente}* — ${row.cliente}, ${row.sucursal}\n` +
    `🖨️ ${row.modelo} — ${row.tecnico}\n` +
    `📅 ${formatFecha(row.fecha_operativo)} · vencido *${row.horas_vencido}h* (SLA ${row.sla_horas}h)`
  );
}

function agruparPorAgente(incidentes: IncidenteVencido[]): [string, IncidenteVencido[]][] {
  const grupos = new Map<string, IncidenteVencido[]>();
  for (const row of incidentes) {
    const lista = grupos.get(row.agente) ?? [];
    lista.push(row);
    grupos.set(row.agente, lista);
  }
  // Agente con más vencidos primero — el más urgente de resolver arriba.
  return [...grupos.entries()].sort((a, b) => b[1].length - a[1].length);
}

export function formatearTablaWhatsapp(
  incidentes: IncidenteVencido[],
  periodoLabel: string,
): string {
  const bloques = agruparPorAgente(incidentes).map(([agente, filas]) =>
    [`👤 *${agente}* (${filas.length})`, "", filas.map(formatearIncidente).join("\n\n")].join(
      "\n",
    ),
  );

  return [
    `📋 *Tablero SLA — vencidos ${periodoLabel}*`,
    `${incidentes.length} incidentes`,
    "",
    bloques.join("\n\n\n"),
  ].join("\n");
}
