"use client";

import type { AnexoPendiente, AnexosPendientesResumen } from "../types/anexos-pendientes";
import {
  ESTADO_META,
  formatImporteUsd,
  formatPeriodo,
} from "./anexos-pendientes-tabla";
import { formatFecha } from "./equipos-sin-real-tabla";

/** Hoja de impresión del reporte — oculta en pantalla, es lo único visible
 * al imprimir (regla `.print-area` en globals.css). Colores claros literales
 * a propósito: la app corre en dark y los tokens del theme imprimirían
 * texto blanco sobre fondo transparente. */
export function AnexosPendientesPrintSheet({
  rows,
  resumen,
}: {
  rows: AnexoPendiente[];
  resumen: AnexosPendientesResumen | null;
}) {
  return (
    <div className="print-area hidden bg-white text-black print:block">
      <h1 className="text-lg font-extrabold uppercase">
        Cierre de contadores — Anexos sin facturar
      </h1>
      <p className="mb-3 text-[11px] text-neutral-600">
        Anexos de Impresión con período abierto (EN PROCESO / DEMORADO) · Fuente: Siges
        {resumen && <> · Período en proceso: {formatPeriodo(resumen.periodo_referencia)}</>} ·
        Impreso el {new Date().toLocaleString("es-AR")}
      </p>
      <table className="w-full border-collapse text-[10px]">
        <thead>
          <tr>
            {[
              "Grupo",
              "Contrato",
              "Anexo",
              "Operador",
              "E. Admin",
              "Vendedor",
              "Moneda",
              "Moneda fact.",
              "Período",
              "Fecha",
              "Estado",
              "USD",
            ].map((h) => (
              <th
                key={h}
                className="border border-neutral-400 bg-neutral-100 px-1.5 py-1 text-left font-bold uppercase"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((a) => (
            <tr key={a.id_anexo}>
              <td className="border border-neutral-300 px-1.5 py-0.5">{a.grupo ?? ""}</td>
              <td className="border border-neutral-300 px-1.5 py-0.5">{a.contrato ?? ""}</td>
              <td className="border border-neutral-300 px-1.5 py-0.5">{a.anexo}</td>
              <td className="border border-neutral-300 px-1.5 py-0.5">
                {a.operador_nombre ?? ""}
              </td>
              <td className="border border-neutral-300 px-1.5 py-0.5">
                {a.empresa_admin ?? ""}
              </td>
              <td className="border border-neutral-300 px-1.5 py-0.5">{a.vendedor ?? ""}</td>
              <td className="border border-neutral-300 px-1.5 py-0.5">{a.moneda ?? ""}</td>
              <td className="border border-neutral-300 px-1.5 py-0.5">
                {a.moneda_facturacion ?? ""}
              </td>
              <td className="border border-neutral-300 px-1.5 py-0.5">{a.periodo}</td>
              <td className="border border-neutral-300 px-1.5 py-0.5">
                {formatFecha(a.fecha_proceso)}
              </td>
              <td className="border border-neutral-300 px-1.5 py-0.5 font-bold">
                {ESTADO_META[a.estado].label.toUpperCase()}
              </td>
              <td className="border border-neutral-300 px-1.5 py-0.5 text-right tabular-nums">
                {formatImporteUsd(a.importe_usd)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-2 text-[10px] text-neutral-600">{rows.length} anexos pendientes</p>
    </div>
  );
}
