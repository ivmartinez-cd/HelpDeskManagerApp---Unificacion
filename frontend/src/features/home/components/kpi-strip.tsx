"use client";

import Link from "next/link";
import type { KpiTile, KpiTone } from "../config/kpi-tiles";
import { cn } from "@/shared/utils/cn";

const DOT: Record<KpiTone, string> = {
  neutral: "bg-muted-foreground/40",
  ok: "bg-success",
  warn: "bg-warning",
  bad: "bg-destructive",
};

function Tile({ t }: { t: KpiTile }) {
  return (
    <Link
      href={t.href}
      aria-label={`${t.label}: ${t.loading ? "cargando" : t.error ? "sin datos" : t.value}`}
      className="group flex min-w-0 flex-col gap-0.5 rounded-[12px] border border-border bg-card px-3.5 py-2.5 no-underline transition-colors hover:border-brand-orange/50 short:px-3 short:py-2"
    >
      <span className="flex items-center gap-1.5 font-heading text-[10.5px] font-bold uppercase tracking-[.05em] text-muted-foreground">
        {t.tone !== "neutral" && !t.loading && !t.error && (
          <span className={cn("h-1.5 w-1.5 shrink-0 rounded-full", DOT[t.tone])} aria-hidden="true" />
        )}
        <span className="truncate">{t.label}</span>
      </span>
      {t.loading ? (
        <span className="mt-1 h-6 w-16 animate-pulse rounded bg-muted short:h-5" aria-hidden="true" />
      ) : (
        <span
          className={cn(
            "font-heading text-[24px] font-extrabold leading-none tabular-nums short:text-[20px]",
            t.error ? "text-muted-foreground" : t.tone === "bad" ? "text-destructive" : "text-foreground",
          )}
        >
          {t.error ? "—" : t.value}
        </span>
      )}
      <span className="truncate font-body text-[11.5px] text-muted-foreground short:text-[11px]">
        {t.loading ? "cargando…" : t.error ? "no se pudo cargar" : t.context}
      </span>
    </Link>
  );
}

/** Capa "resumen" del dashboard: 5–8 tiles de estado en una sola fila, lo
 * primero que mira el ojo. Cada tile navega a su pantalla. */
export function KpiStrip({ tiles }: { tiles: KpiTile[] }) {
  if (tiles.length === 0) return null;
  return (
    <div
      data-testid="kpi-strip"
      className="grid flex-none gap-3 short:gap-2.5"
      style={{ gridTemplateColumns: `repeat(${tiles.length}, minmax(0, 1fr))` }}
    >
      {tiles.map((t) => (
        <Tile key={t.id} t={t} />
      ))}
    </div>
  );
}
