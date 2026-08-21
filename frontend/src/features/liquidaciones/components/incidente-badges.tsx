"use client";

/** Badges de estado/tipo de `incidente-row.tsx`, extraídos de
 * `incidentes-tabla.tsx` porque ese archivo ya superaba el tamaño máximo de
 * archivo (§4). */

export function EstadoValidacionBadge({ estado }: { estado: string }) {
  if (estado === "ok")
    return <span className="font-body text-xs font-semibold text-success">● OK</span>;
  if (estado === "con_alertas")
    return <span className="font-body text-xs font-semibold text-destructive">● CON ALERTAS</span>;
  return <span className="font-body text-xs text-muted-foreground">{estado}</span>;
}

export function TipoBadge({ tipo }: { tipo: string }) {
  const lower = tipo.toLowerCase();
  const cls =
    lower === "correctivo"
      ? "bg-brand-orange/15 text-brand-orange"
      : lower === "preventivo"
        ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400"
        : "";
  return cls ? (
    <span className={`rounded-[6px] px-2 py-0.5 font-body text-xs font-semibold ${cls}`}>
      {tipo}
    </span>
  ) : (
    <span className="font-body text-xs text-muted-foreground">{tipo}</span>
  );
}

export function riesgoClass(riesgo: number) {
  if (riesgo > 0.7) return "text-destructive";
  if (riesgo > 0.3) return "text-warning";
  return "text-success";
}
