import type { IncidenteDerivado } from "../types/derivados";
import type { IncidenteMesaAyuda } from "../types/mesa-ayuda";
import type { IncidenteSinCerrar } from "../types/pendientes";
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

// Mismos criterios de agrupado/anclas que arriba, adaptados a cada shape de
// "Incidentes sin consultar" / "Pendientes a Cerrar" / "Mesa de Ayuda" — no
// comparten columnas con IncidenteVencido así que no reutilizan sus formatters.

function agruparPor<T>(incidentes: T[], clave: (row: T) => string): [string, T[]][] {
  const grupos = new Map<string, T[]>();
  for (const row of incidentes) {
    const lista = grupos.get(clave(row)) ?? [];
    lista.push(row);
    grupos.set(clave(row), lista);
  }
  return [...grupos.entries()].sort((a, b) => b[1].length - a[1].length);
}

function formatearIncidenteDerivado(row: IncidenteDerivado): string {
  const marca = row.demorado ? "🔴" : "🟡";
  return (
    `${marca} *#${row.id_incidente}* — ${row.cliente}, ${row.sucursal}\n` +
    `🖨️ ${row.modelo} — ${row.tecnico}\n` +
    `📅 Ingreso ${formatFecha(row.fecha_ingreso)} · sin consultar hace *${row.dias_desde_ingreso} día(s)*`
  );
}

export function formatearDerivadosWhatsapp(
  incidentes: IncidenteDerivado[],
  periodoLabel: string,
): string {
  const bloques = agruparPor(incidentes, (row) => row.tecnico).map(([tecnico, filas]) =>
    [
      `👤 *${tecnico}* (${filas.length})`,
      "",
      filas.map(formatearIncidenteDerivado).join("\n\n"),
    ].join("\n"),
  );

  return [
    `📋 *Incidentes sin consultar — ${periodoLabel}*`,
    `${incidentes.length} incidentes`,
    "",
    bloques.join("\n\n\n"),
  ].join("\n");
}

function formatearPendienteACerrar(row: IncidenteSinCerrar): string {
  const marca = row.dias_en_estado >= 30 ? "🔴" : "🟡";
  return (
    `${marca} *#${row.id_incidente}* — ${row.cliente}, ${row.sucursal}\n` +
    `🖨️ ${row.modelo} — ${row.tecnico}\n` +
    `📅 Ingreso ${formatFecha(row.fecha_ingreso)} → Finalizado ${formatFecha(row.fecha_finalizacion)} · *${row.dias_en_estado} día(s)* sin cerrar`
  );
}

export function formatearPendientesACerrarWhatsapp(incidentes: IncidenteSinCerrar[]): string {
  const bloques = agruparPor(incidentes, (row) => row.tecnico).map(([tecnico, filas]) =>
    [
      `👤 *${tecnico}* (${filas.length})`,
      "",
      filas.map(formatearPendienteACerrar).join("\n\n"),
    ].join("\n"),
  );

  return [
    `📋 *Pendientes a Cerrar*`,
    `${incidentes.length} incidentes`,
    "",
    bloques.join("\n\n\n"),
  ].join("\n");
}

function formatearIncidenteMesaAyuda(row: IncidenteMesaAyuda): string {
  const marca = row.demorado ? "🔴" : "🟡";
  return (
    `${marca} *#${row.id_incidente}* — ${row.cliente}, ${row.sucursal}\n` +
    `🖨️ ${row.modelo}\n` +
    `📅 Ingreso ${formatFecha(row.fecha_ingreso)} · *${row.dias_transcurridos} día(s)* transcurridos`
  );
}

export function formatearMesaAyudaWhatsapp(incidentes: IncidenteMesaAyuda[]): string {
  const bloques = agruparPor(incidentes, (row) => row.operador).map(([operador, filas]) =>
    [
      `👤 *${operador}* (${filas.length})`,
      "",
      filas.map(formatearIncidenteMesaAyuda).join("\n\n"),
    ].join("\n"),
  );

  return [
    `📋 *Incidentes Mesa de Ayuda*`,
    `${incidentes.length} incidentes`,
    "",
    bloques.join("\n\n\n"),
  ].join("\n");
}
