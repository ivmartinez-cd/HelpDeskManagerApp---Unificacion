"use client";

import { CheckCircle2, CalendarCheck2, ChevronDown } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import type {
  CalendarEvent,
  ClientesPendientesPeriodo,
  ResumenClientesOperador,
} from "@/features/contadores/types/calendario";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import { DashboardCard } from "./dashboard-card";

const DIA_CIERRE = 20;

function fmtDiaMes(d: Date): string {
  return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}`;
}

/**
 * El ciclo de cierre rota el día DIA_CIERRE de cada mes. Del día 1 al 20
 * seguimos "hacia" el cierre de este mes; desde el 21 ya arrancó el ciclo
 * siguiente y lo que quedó del anterior pasa a ser arrastre.
 */
function getCicloCierre(hoy: Date) {
  const hoyMid = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());
  const cierreEsteMes = new Date(hoy.getFullYear(), hoy.getMonth(), DIA_CIERRE);
  const enArrastre = hoyMid.getTime() > cierreEsteMes.getTime();
  const proximoCierre = enArrastre
    ? new Date(hoy.getFullYear(), hoy.getMonth() + 1, DIA_CIERRE)
    : cierreEsteMes;
  const diasParaCierre = Math.round((proximoCierre.getTime() - hoyMid.getTime()) / 86_400_000);
  return { enArrastre, labelProximoCierre: fmtDiaMes(proximoCierre), diasParaCierre };
}

function badgeToneFuera(cantidad: number | null) {
  if (cantidad === null) return "bg-border/60 text-muted-foreground";
  if (cantidad === 0) return "bg-emerald-500/15 text-emerald-400";
  return "bg-red-500/15 text-red-400";
}

function badgeToneDentro(sinCerrar: number, diasParaCierre: number) {
  if (sinCerrar === 0) return "bg-emerald-500/15 text-emerald-400";
  if (diasParaCierre > 5) return "bg-amber-500/15 text-amber-400";
  return "bg-red-500/15 text-red-400";
}

function ArrastreBlock({
  data,
  loading,
}: {
  data: ClientesPendientesPeriodo | null;
  loading: boolean;
}) {
  if (data === null) {
    return (
      <div className="rounded-lg border border-border/60 p-2.5">
        <span className="font-body text-[12px] text-muted-foreground">
          {loading
            ? "Verificando arrastre del cierre anterior…"
            : "No se pudo verificar el arrastre del cierre anterior."}
        </span>
      </div>
    );
  }
  if (data.cantidad === null) {
    return (
      <div className="rounded-lg border border-border/60 p-2.5">
        <span className="font-body text-[12px] text-muted-foreground">
          No se pudo verificar el arrastre del cierre anterior.
        </span>
      </div>
    );
  }
  if (data.cantidad === 0) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-2.5">
        <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
        <span className="font-body text-[12px] font-semibold text-emerald-400">
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
    <div className="rounded-lg border border-red-500/20 bg-red-500/5">
      <button
        type="button"
        onClick={() => puedeExpandir && setOpen((prev) => !prev)}
        aria-expanded={open}
        className={cn(
          "flex w-full items-baseline gap-1.5 p-2.5 text-left",
          puedeExpandir && "cursor-pointer",
        )}
      >
        <span className="font-heading text-[22px] font-extrabold tabular-nums leading-none text-red-400">
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
        <ul className="flex flex-col gap-1 border-t border-red-500/20 px-2.5 py-2">
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

export function CierreMensualCard({
  pendientes,
  resumen,
  pendientesPeriodoAnterior,
  pendientesPeriodoAnteriorLoading,
  loading,
  error,
}: {
  pendientes: CalendarEvent[];
  resumen: ResumenClientesOperador | null;
  pendientesPeriodoAnterior: ClientesPendientesPeriodo | null;
  pendientesPeriodoAnteriorLoading: boolean;
  loading: boolean;
  error: string | null;
}) {
  const sinCerrar = pendientes.length;
  const total = resumen?.total_clientes ?? null;
  const cerrados = total !== null ? Math.max(0, total - sinCerrar) : null;
  const pct = cerrados !== null && total && total > 0 ? (cerrados / total) * 100 : null;
  const { enArrastre, labelProximoCierre, diasParaCierre } = getCicloCierre(new Date());
  const badgeTone = enArrastre
    ? badgeToneFuera(pendientesPeriodoAnterior?.cantidad ?? null)
    : badgeToneDentro(sinCerrar, diasParaCierre);

  return (
    <DashboardCard
      icon={CalendarCheck2}
      title="Cierre mensual"
      subtitle="Contadores del mes · Validación de cierre"
      loading={loading}
      error={error}
      headerRight={
        !loading && !error ? (
          <span
            className={`shrink-0 rounded-full px-2.5 py-0.5 font-heading text-[12px] font-extrabold ${badgeTone}`}
          >
            {labelProximoCierre}
          </span>
        ) : undefined
      }
    >
      <div className="mt-3 flex flex-col gap-3">
        {enArrastre ? (
          <>
            <div className="flex items-baseline gap-1.5 pt-1">
              {total !== null && (
                <span className="font-heading text-[36px] font-extrabold tabular-nums leading-none text-foreground">
                  {total}
                </span>
              )}
              <span className="font-body text-[13px] text-muted-foreground">
                clientes por cerrar antes del {labelProximoCierre}
              </span>
            </div>
            <span className="font-body text-[11px] text-muted-foreground">
              Nuevo período en curso · faltan {diasParaCierre}{" "}
              {diasParaCierre === 1 ? "día" : "días"}
            </span>
            <ArrastreBlock
              data={pendientesPeriodoAnterior}
              loading={pendientesPeriodoAnteriorLoading}
            />
          </>
        ) : sinCerrar === 0 ? (
          <div className="flex items-center gap-2 pt-1">
            <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-400" />
            <span className="font-heading text-[15px] font-extrabold text-emerald-400">
              Todos cerrados
            </span>
          </div>
        ) : (
          <>
            <div className="flex items-baseline gap-1.5 pt-1">
              <span
                className={`font-heading text-[36px] font-extrabold tabular-nums leading-none ${
                  diasParaCierre > 5 ? "text-amber-400" : "text-red-400"
                }`}
              >
                {sinCerrar}
              </span>
              <span className="font-body text-[13px] text-muted-foreground">
                {sinCerrar === 1 ? "cliente sin cerrar" : "clientes sin cerrar"}
                {total !== null && <> de {total}</>}
              </span>
            </div>
            {pct !== null && (
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-border/60">
                <div
                  className="h-full rounded-full bg-brand-orange transition-all"
                  style={{ width: `${pct}%` }}
                />
              </div>
            )}
            <span className="font-body text-[11px] text-muted-foreground">
              {diasParaCierre > 0
                ? `${diasParaCierre} ${diasParaCierre === 1 ? "día" : "días"} para el cierre`
                : "Cierre hoy"}
            </span>
          </>
        )}

        <Link href="/contadores/anexos-pendientes" className={cn(brandButtonClasses(), "mt-0.5 w-full")}>
          Ver anexos sin facturar →
        </Link>
      </div>
    </DashboardCard>
  );
}
