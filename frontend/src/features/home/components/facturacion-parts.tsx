"use client";

import { CheckCircle2, ChevronDown } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import type {
  CalendarEvent,
  ClientesPendientesPeriodo,
  Operador,
} from "@/features/contadores/types/calendario";
import {
  cleanTitle,
  diasDeAtraso,
  formatDateLocal,
  operadorEfectivo,
  textoAtraso,
} from "@/features/contadores/utils/calendario-format";
import { cn } from "@/shared/utils/cn";
import { AGING_BUCKETS, agingDotColor, fmtInt } from "../utils/inicio-format";

export const DIA_CIERRE = 20;

function fmtDiaMes(d: Date): string {
  return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}`;
}

/** El ciclo de cierre rota el día DIA_CIERRE de cada mes. Del 1 al 20 vamos
 * "hacia" el cierre de este mes; desde el 21 arrancó el ciclo siguiente y lo
 * que quedó del anterior pasa a ser arrastre. */
export function getCicloCierre(hoy: Date) {
  const hoyMid = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());
  const cierreEsteMes = new Date(hoy.getFullYear(), hoy.getMonth(), DIA_CIERRE);
  const enArrastre = hoyMid.getTime() > cierreEsteMes.getTime();
  const proximoCierre = enArrastre
    ? new Date(hoy.getFullYear(), hoy.getMonth() + 1, DIA_CIERRE)
    : cierreEsteMes;
  const diasParaCierre = Math.round((proximoCierre.getTime() - hoyMid.getTime()) / 86_400_000);
  return { enArrastre, labelProximoCierre: fmtDiaMes(proximoCierre), diasParaCierre };
}

export interface Pendiente {
  id: string;
  nombre: string;
  operador: string | null;
  dias: number;
}

export function prepararPendientes(eventos: CalendarEvent[], operadores: Operador[]): Pendiente[] {
  const hoy = formatDateLocal(new Date());
  return eventos
    .map((evt) => ({
      id: evt.id,
      nombre: evt.cliente || cleanTitle(evt.title) || "Sin nombre",
      operador: operadorEfectivo(evt, operadores)?.nombre ?? null,
      dias: diasDeAtraso(evt.start, hoy),
    }))
    .sort((a, b) => b.dias - a.dias);
}

/** Arrastre del cierre anterior (solo después del día 20). */
export function ArrastreBlock({
  data,
  loading,
}: {
  data: ClientesPendientesPeriodo | null;
  loading: boolean;
}) {
  if (data === null || data.cantidad === null) {
    return (
      <div className="rounded-[8px] border border-border/60 px-2.5 py-2 font-body text-[12px] text-muted-foreground">
        {loading && data === null
          ? "Verificando arrastre del cierre anterior…"
          : "No se pudo verificar el arrastre del cierre anterior."}
      </div>
    );
  }
  if (data.cantidad === 0) {
    return (
      <div className="flex items-center gap-2 rounded-[8px] border border-success/25 bg-success/5 px-2.5 py-2">
        <CheckCircle2 className="h-4 w-4 shrink-0 text-success" />
        <span className="font-body text-[12px] font-semibold text-success">
          Sin arrastre del cierre anterior
        </span>
      </div>
    );
  }
  return <ArrastreDetalle cantidad={data.cantidad} grupos={data.grupos} />;
}

function ArrastreDetalle({ cantidad, grupos }: { cantidad: number; grupos: string[] | null }) {
  const [open, setOpen] = useState(false);
  const puedeExpandir = grupos !== null && grupos.length > 0;
  return (
    <div className="rounded-[8px] border border-destructive/25 bg-destructive/5">
      <button
        type="button"
        onClick={() => puedeExpandir && setOpen((prev) => !prev)}
        aria-expanded={open}
        className={cn(
          "flex w-full items-baseline gap-1.5 px-2.5 py-2 text-left",
          puedeExpandir && "cursor-pointer",
        )}
      >
        <span className="font-heading text-[20px] font-extrabold leading-none text-destructive tabular-nums">
          {cantidad}
        </span>
        <span className="font-body text-[12px] text-muted-foreground">
          {cantidad === 1 ? "cliente" : "clientes"} con cierre pendiente del período anterior
        </span>
        {puedeExpandir && (
          <ChevronDown
            className={cn(
              "ml-auto h-4 w-4 shrink-0 text-muted-foreground transition-transform",
              open && "rotate-180",
            )}
          />
        )}
      </button>
      {open && grupos && (
        <ul className="flex flex-col gap-1 border-t border-destructive/20 px-2.5 py-2">
          {grupos.map((grupo) => (
            <li key={grupo} className="font-body text-[12px] text-muted-foreground">
              {grupo}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

const SIN_VENCER_COLOR = "#3b82f6";

/** Antigüedad de los pendientes en buckets, como barras horizontales CSS
 * (longitud, no ángulo; sin Chart.js para pocos números). Durante el
 * arrastre `pendientes` puede traer días <= 0 (todavía no llegó la fecha,
 * ver período en curso): esos van aparte en "Sin vencer" en vez de forzarlos
 * en el bucket "1-2 días" — no se toca `AGING_BUCKETS` (comparte índices con
 * el KPI de arriba, ver kpi-tiles.ts). */
export function BucketsAntiguedad({ pendientes }: { pendientes: Pendiente[] }) {
  const sinVencer = pendientes.filter((p) => p.dias <= 0).length;
  const conteos = AGING_BUCKETS.map(
    (b) => pendientes.filter((p) => p.dias >= Math.max(b.min, 1) && p.dias <= b.max).length,
  );
  const max = Math.max(1, sinVencer, ...conteos);
  return (
    <div className="grid grid-cols-[58px_minmax(0,1fr)_24px] items-center gap-x-2 gap-y-0.5">
      {sinVencer > 0 && (
        <div className="contents">
          <span className="font-body text-[11px] text-muted-foreground">Sin vencer</span>
          <span className="h-2 overflow-hidden rounded-full bg-surface-2">
            <span
              className="block h-full rounded-full"
              style={{ width: `${(sinVencer / max) * 100}%`, background: SIN_VENCER_COLOR }}
            />
          </span>
          <span className="text-right font-heading text-[11.5px] font-bold tabular-nums text-foreground">
            {sinVencer}
          </span>
        </div>
      )}
      {AGING_BUCKETS.map((b, i) => (
        <div key={b.label} className="contents">
          <span className="font-body text-[11px] text-muted-foreground">{b.label}</span>
          <span className="h-2 overflow-hidden rounded-full bg-surface-2">
            <span
              className="block h-full rounded-full"
              style={{ width: `${(conteos[i] / max) * 100}%`, background: b.color }}
            />
          </span>
          <span className="text-right font-heading text-[11.5px] font-bold tabular-nums text-foreground">
            {conteos[i]}
          </span>
        </div>
      ))}
    </div>
  );
}

export function PendientesLista({ pendientes, top }: { pendientes: Pendiente[]; top: number }) {
  return (
    <ul className="flex flex-col gap-1">
      {pendientes.slice(0, top).map((p) => (
        <li key={p.id} className="flex items-center gap-2">
          <span
            className="h-[7px] w-[7px] shrink-0 rounded-full"
            style={{ background: agingDotColor(p.dias) }}
          />
          <span className="min-w-0 flex-1 truncate font-body text-[12px] font-semibold text-foreground/80">
            {p.nombre}
            {p.operador && <span className="font-normal text-muted-foreground"> · {p.operador}</span>}
          </span>
          <span
            className="shrink-0 font-body text-[11px] font-semibold tabular-nums"
            style={{ color: agingDotColor(p.dias) }}
          >
            {textoAtraso(p.dias)}
          </span>
        </li>
      ))}
      {pendientes.length > top && (
        <li>
          <Link
            href="/contadores/calendario"
            className="font-body text-[11.5px] font-semibold text-muted-foreground no-underline hover:text-brand-orange"
          >
            y {fmtInt(pendientes.length - top)} más…
          </Link>
        </li>
      )}
    </ul>
  );
}
