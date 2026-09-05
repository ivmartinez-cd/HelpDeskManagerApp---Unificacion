"use client";

import { useEffect, useState } from "react";
import { FileText } from "lucide-react";
import { liquidacionesApi } from "../api/liquidaciones-api";
import { formatARS } from "../lib/format";
import type { Liquidacion } from "../types/liquidaciones";

const TIPO_ABONO = "abono";
const MAX_HISTORIAL = 6;

/** Aviso para liquidaciones de abono (contrato mensual, caso SAN JUAN): los
 * incidentes vienen a $1 y el importe real es el ítem extra que el prestador
 * carga en AyC. El motor ya no genera alertas de precio acá; lo único a
 * controlar es que el extra esté cargado, y como el monto varía siempre
 * (decisión del usuario 2026-09-05: sin alerta por monto) se muestran los
 * últimos abonos del mismo prestador para que la TL compare a ojo. */
export function AbonoBanner({
  liquidacion,
  totalIncidentes,
}: {
  liquidacion: Liquidacion;
  totalIncidentes: number;
}) {
  const [historial, setHistorial] = useState<Liquidacion[] | null>(null);
  const esAbono = liquidacion.tipoLiquidacion === TIPO_ABONO;

  useEffect(() => {
    if (!esAbono) return;
    liquidacionesApi
      .list({ prestadorId: liquidacion.prestadorId, size: 200 })
      .then((page) =>
        setHistorial(
          page.items
            .filter(
              (l) =>
                l.id !== liquidacion.id && l.tipoLiquidacion === TIPO_ABONO && l.montoExtra !== null,
            )
            .sort((a, b) => b.periodo.localeCompare(a.periodo))
            .slice(0, MAX_HISTORIAL),
        ),
      )
      .catch(() => setHistorial([]));
  }, [esAbono, liquidacion.id, liquidacion.prestadorId]);

  if (!esAbono) return null;
  const sinExtra = liquidacion.montoExtra === null;

  return (
    <div
      className={`flex items-start gap-3 rounded-[12px] border px-5 py-4 ${
        sinExtra ? "border-brand-orange/30 bg-brand-orange/10" : "border-border bg-muted/40"
      }`}
    >
      <FileText size={16} className="mt-0.5 flex-shrink-0 text-brand-orange" />
      <div className="flex flex-col gap-1 font-body text-sm text-foreground">
        <p className="font-semibold">
          Liquidación de abono: los {totalIncidentes} incidentes vienen a $1 y el importe real es
          el ítem extra.
        </p>
        {sinExtra ? (
          <p className="text-muted-foreground">
            Falta el ítem extra. Se toma solo de Canal Directo cuando el prestador lo carga; no
            aprobar hasta entonces.
          </p>
        ) : (
          <p className="text-muted-foreground">
            Extra cargado: {formatARS(liquidacion.montoExtra ?? 0)}
            {liquidacion.conceptoExtra ? ` — ${liquidacion.conceptoExtra}` : ""}
          </p>
        )}
        {historial && historial.length > 0 && (
          <div className="mt-1">
            <p className="text-xs font-semibold uppercase tracking-[.06em] text-muted-foreground">
              Últimos abonos del prestador
            </p>
            <ul className="mt-0.5 text-xs text-muted-foreground">
              {historial.map((l) => (
                <li key={l.id}>
                  {l.periodo} · {formatARS(l.montoExtra ?? 0)}
                  {l.conceptoExtra ? ` — ${l.conceptoExtra}` : ""}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
