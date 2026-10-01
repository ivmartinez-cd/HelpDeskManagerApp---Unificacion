import type { AnexoPendiente } from "../types/anexos-pendientes";
import { formatImporteUsd, formatPeriodo } from "../components/anexos-pendientes-tabla";

// Mismo criterio que `features/sla/lib/formato-whatsapp.ts`: agrupado — acá
// por grupo de cliente — con anclas en negrita y emoji de estado (WhatsApp no
// soporta texto de color). `fecha_proceso` es date-only ("YYYY-MM-DD"),
// mismo motivo que `formatFecha` de `equipos-sin-real-tabla.tsx`.

function formatFecha(iso: string): string {
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year}`;
}

const ESTADO_MARCA: Record<AnexoPendiente["estado"], string> = {
  demorado: "🔴",
  en_proceso: "🟡",
  mes_en_curso: "⚪",
};

function formatearAnexo(fila: AnexoPendiente): string {
  const marca = ESTADO_MARCA[fila.estado];
  const contratoLine =
    fila.contrato && fila.contrato !== fila.anexo ? ` (${fila.contrato})` : "";
  return (
    `${marca} *${fila.anexo}*${contratoLine}\n` +
    `🏢 ${fila.empresa_admin ?? "—"}${fila.vendedor ? ` · Vendedor: ${fila.vendedor}` : ""}\n` +
    `📅 Período ${formatPeriodo(fila.periodo)} (${formatFecha(fila.fecha_proceso)}) · USD ${formatImporteUsd(fila.importe_usd)}`
  );
}

function agruparPorGrupo(filas: AnexoPendiente[]): [string, AnexoPendiente[]][] {
  const grupos = new Map<string, AnexoPendiente[]>();
  for (const fila of filas) {
    const clave = fila.grupo ?? "Sin grupo";
    const lista = grupos.get(clave) ?? [];
    lista.push(fila);
    grupos.set(clave, lista);
  }
  return [...grupos.entries()].sort((a, b) => a[0].localeCompare(b[0], "es"));
}

export function formatearAnexosPendientesWhatsapp(
  filas: AnexoPendiente[],
  periodoLabel: string,
): string {
  const bloques = agruparPorGrupo(filas).map(([grupo, filasGrupo]) =>
    [`📁 *${grupo}* (${filasGrupo.length})`, "", filasGrupo.map(formatearAnexo).join("\n\n")].join(
      "\n",
    ),
  );

  return [
    `📋 *Anexos sin facturar — ${periodoLabel}*`,
    `${filas.length} anexo${filas.length !== 1 ? "s" : ""}`,
    "",
    bloques.join("\n\n\n"),
  ].join("\n");
}
