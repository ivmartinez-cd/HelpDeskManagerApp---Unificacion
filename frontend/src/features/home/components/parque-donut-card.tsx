"use client";

import { Printer } from "lucide-react";
import Link from "next/link";
import type { PrestadoresResumen } from "@/features/prestadores/types/prestadores";
import { brandButtonClasses } from "@/shared/components/ui/brand-form";
import { cn } from "@/shared/utils/cn";
import { FALLBACK_COLOR } from "../utils/inicio-format";
import { DashboardCard } from "./dashboard-card";
import { OperadorDonut, type DonutRow } from "./operador-donut";

/** Suma el parque (equipos de los PST activos) por operador — el conteo de
 * equipos viene en vivo desde Siges. "Sin asignar" va al final. */
export function agruparParque(resumen: PrestadoresResumen): DonutRow[] {
  const filas = resumen.grupos.flatMap((grupo) => {
    const activos = grupo.prestadores.filter((p) => p.isActive);
    if (activos.length === 0) return [];
    return [
      {
        id: grupo.operadorId ?? "sin-asignar",
        nombre: grupo.operadorNombre ?? "Sin asignar",
        detalle: `${activos.length} PST`,
        color: grupo.operadorColor ?? FALLBACK_COLOR,
        valor: activos.reduce((sum, p) => sum + (p.equipos ?? 0), 0),
      },
    ];
  });
  return filas.sort((a, b) => {
    if (a.id === "sin-asignar") return 1;
    if (b.id === "sin-asignar") return -1;
    return b.valor - a.valor;
  });
}

export function ParqueDonutCard({
  resumen,
  loading,
  error,
}: {
  resumen: PrestadoresResumen | null;
  loading: boolean;
  error: string | null;
}) {
  const rows = resumen ? agruparParque(resumen) : [];
  const total = rows.reduce((sum, r) => sum + r.valor, 0);

  return (
    <DashboardCard
      icon={Printer}
      title="Distribución del parque"
      subtitle="Impresoras por operador"
      loading={loading}
      error={error}
    >
      {rows.length === 0 ? (
        <span className="pt-3 font-body text-[13px] text-muted-foreground">
          No hay prestadores activos cargados.
        </span>
      ) : (
        <>
          <OperadorDonut rows={rows} total={total} centerSub="impresoras" tooltipUnidad="impresoras" />
          <Link href="/prestadores" className={cn(brandButtonClasses(), "mt-3.5 w-full")}>
            Ver prestadores →
          </Link>
        </>
      )}
    </DashboardCard>
  );
}
