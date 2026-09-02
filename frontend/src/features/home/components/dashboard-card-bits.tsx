"use client";

import { Inbox, TriangleAlert } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { cn } from "@/shared/utils/cn";
import { useNow } from "../hooks/use-now";
import { minutosDesde, textoHace } from "../utils/inicio-format";

/** Link de pie de card ("Ver detalle →"): texto naranja, sin botón. El
 * botón primario queda reservado a la única acción que sí hay que hacer ahora. */
export function CardLink({
  href,
  children,
  external = false,
}: {
  href: string;
  children: ReactNode;
  external?: boolean;
}) {
  const className =
    "font-body text-[12.5px] font-semibold text-brand-orange no-underline hover:text-brand-orange-hover";
  if (external) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className={className}>
        {children}
      </a>
    );
  }
  return (
    <Link href={href} className={className}>
      {children}
    </Link>
  );
}

/** Estado vacío compacto: una línea con ícono tenue, sin botones grandes. */
export function CardEmpty({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-1 items-center gap-2 py-2 font-body text-[13px] text-muted-foreground">
      <Inbox className="h-4 w-4 shrink-0 opacity-60" aria-hidden="true" />
      <span>{children}</span>
    </div>
  );
}

/** Frescura unificada ("Actualizado hace 12 min"); pasa a tono warning con
 * ícono cuando supera `staleAfterMin`. */
export function Freshness({
  at,
  staleAfterMin,
  prefix = "Actualizado",
  className,
}: {
  at: string | null | undefined;
  staleAfterMin?: number;
  prefix?: string;
  className?: string;
}) {
  const now = useNow(30_000);
  if (!now) return null;
  const mins = minutosDesde(at, now.getTime());
  const stale = staleAfterMin !== undefined && (mins === null || mins > staleAfterMin);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-body text-[11px]",
        stale ? "font-semibold text-warning" : "text-muted-foreground",
        className,
      )}
      title={stale ? "El dato puede estar desactualizado" : undefined}
    >
      {stale && <TriangleAlert className="h-3 w-3 shrink-0" aria-hidden="true" />}
      {prefix} {textoHace(at, now.getTime())}
    </span>
  );
}

/** Badge numérico del header (tono semántico por estado). */
export function CountBadge({
  value,
  tone = "neutral",
}: {
  value: number | string;
  tone?: "neutral" | "ok" | "warn" | "bad" | "brand";
}) {
  const tones = {
    neutral: "bg-muted text-muted-foreground",
    ok: "bg-success/15 text-success",
    warn: "bg-warning/20 text-warning-foreground dark:text-warning",
    bad: "bg-destructive/15 text-destructive",
    brand: "bg-brand-orange/15 text-brand-orange",
  } as const;
  return (
    <span
      className={cn(
        "rounded-full px-2 py-0.5 font-heading text-[12px] font-bold tabular-nums",
        tones[tone],
      )}
    >
      {value}
    </span>
  );
}

/** Mini estadística en fila (label caps 11 + valor 15) para cuerpos de card. */
export function MiniStat({
  label,
  value,
  className,
}: {
  label: string;
  value: ReactNode;
  className?: string;
}) {
  return (
    <div className="rounded-[8px] bg-surface-2 px-2.5 py-1.5 text-center">
      <div className="font-heading text-[10.5px] font-bold uppercase tracking-[.05em] text-muted-foreground">
        {label}
      </div>
      <div className={cn("mt-0.5 font-heading text-[15px] font-extrabold tabular-nums", className)}>
        {value}
      </div>
    </div>
  );
}

/** Fila "nombre · barra · valor" para comparar categorías por longitud
 * (posición/longitud se leen mejor que el ángulo de una dona). */
export function BarRow({
  color,
  label,
  detail,
  value,
  pct,
  widthPct,
}: {
  color: string;
  label: string;
  detail?: string;
  value: string;
  pct?: string;
  widthPct: number;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="h-[9px] w-[9px] shrink-0 rounded-[3px]" style={{ background: color }} />
      <span className="min-w-0 flex-[0_0_44%] truncate font-body text-[12.5px] font-semibold text-foreground/80">
        {label}
        {detail && <span className="font-normal text-muted-foreground"> · {detail}</span>}
      </span>
      <span className="h-2 min-w-0 flex-1 overflow-hidden rounded-full bg-surface-2">
        <span
          className="block h-full rounded-full"
          style={{ width: `${Math.max(0, Math.min(100, widthPct))}%`, background: color }}
        />
      </span>
      {pct && (
        <span className="w-[42px] shrink-0 text-right font-body text-[11.5px] text-muted-foreground tabular-nums">
          {pct}
        </span>
      )}
      <span className="w-[46px] shrink-0 text-right font-heading text-[12.5px] font-bold tabular-nums text-foreground">
        {value}
      </span>
    </div>
  );
}
