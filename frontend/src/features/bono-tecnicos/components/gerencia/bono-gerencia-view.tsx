"use client";

import { useState } from "react";
import { BonoRankingTable, type BonoRankingSortKey } from "./bono-ranking-table";
import { BonoTecnicoAnualModal } from "./bono-tecnico-anual-modal";
import { useBonoEvolucionAnual } from "../../hooks/use-bono-evolucion-anual";
import type { EvolucionTecnico } from "../../types/bono-tecnicos";
import { TrendChart } from "@/features/insumos/components/shared";
import { BrandSelect } from "@/shared/components/ui/brand-form";
import { KpiGrid, KpiTile } from "@/shared/components/ui/kpi-tile";
import { Spinner } from "@/shared/components/ui/spinner";
import { useTableSort } from "@/shared/hooks/use-table-sort";

const decimalFormat = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 2 });
const MESES = [
  "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
];

function promedioNoNulo(valores: (number | null)[]): number | null {
  const presentes = valores.filter((v): v is number => v !== null);
  if (presentes.length === 0) return null;
  return presentes.reduce((a, b) => a + b, 0) / presentes.length;
}

function aniosDisponibles(): number[] {
  const actual = new Date().getFullYear();
  return [actual, actual - 1, actual - 2];
}

export function BonoGerenciaView() {
  const { anio, setAnio, tecnicos, equipo, loading, error } = useBonoEvolucionAnual();
  const [tecnicoSeleccionado, setTecnicoSeleccionado] = useState<EvolucionTecnico | null>(null);
  const { sort, toggleSort } = useTableSort<BonoRankingSortKey>({
    initial: { key: "puntaje_promedio", direction: "desc" },
    keys: ["tecnico", "puntaje_promedio", "delta", "incidentes", "tv"],
    descFirstKeys: ["puntaje_promedio", "delta", "incidentes", "tv"],
  });

  const promedioEquipo = equipo ? promedioNoNulo(equipo.puntos.map((p) => p.puntaje)) : null;
  const incidentesTotal = tecnicos.reduce((acc, t) => acc + t.incidentes_total, 0);
  const tvAprobadas = tecnicos.reduce((acc, t) => acc + t.tv_aprobadas_total, 0);
  const tvSolicitadas = tecnicos.reduce((acc, t) => acc + t.tv_solicitadas_total, 0);
  const mesesSinDatos = tecnicos.reduce(
    (acc, t) => acc + t.puntos.filter((p) => p.puntaje === null).length,
    0,
  );

  return (
    <div className="flex flex-col gap-6 px-9 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="font-heading text-[25px] font-extrabold text-foreground">
            Bono Técnicos — Gerencia
          </h1>
          <p className="font-body text-sm text-muted-foreground">
            Evolución anual del puntaje por técnico, comparada contra el promedio del equipo.
          </p>
        </div>
        <BrandSelect
          label="Año"
          value={String(anio)}
          onChange={(e) => setAnio(Number(e.target.value))}
        >
          {aniosDisponibles().map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </BrandSelect>
      </div>

      {loading && (
        <div className="flex h-64 items-center justify-center">
          <Spinner />
        </div>
      )}

      {!loading && error && (
        <p className="rounded-[12px] border border-destructive/40 bg-destructive/5 px-6 py-5 font-body text-sm text-foreground">
          {error}
        </p>
      )}

      {!loading && !error && (
        <div className="flex flex-col gap-6">
          <KpiGrid>
            <KpiTile
              label="Puntaje promedio del equipo"
              value={promedioEquipo !== null ? decimalFormat.format(promedioEquipo) : "—"}
              tone="orange"
            />
            <KpiTile label="Incidentes atendidos" value={String(incidentesTotal)} />
            <KpiTile
              label="TV aprobadas"
              value={String(tvAprobadas)}
              hint={`de ${tvSolicitadas} solicitadas`}
            />
            <KpiTile
              label="Meses sin Días cargados"
              value={String(mesesSinDatos)}
              tone={mesesSinDatos > 0 ? "danger" : "neutral"}
              hint="Suma de todos los técnicos, sin puntaje calculado ese mes"
            />
          </KpiGrid>

          {equipo && (
            <TrendChart
              title="Puntaje promedio del equipo"
              labels={equipo.puntos.map((p) => MESES[(p.periodo % 100) - 1])}
              values={equipo.puntos.map((p) => p.puntaje)}
              seriesLabel="Promedio del equipo"
              heightPx={260}
              formatValue={(v) => decimalFormat.format(v)}
            />
          )}

          <BonoRankingTable
            tecnicos={tecnicos}
            promedioEquipo={promedioEquipo}
            sort={sort}
            onToggleSort={toggleSort}
            onVerTecnico={setTecnicoSeleccionado}
          />
        </div>
      )}

      {tecnicoSeleccionado && (
        <BonoTecnicoAnualModal
          key={tecnicoSeleccionado.id_tecnico}
          tecnico={tecnicoSeleccionado}
          equipo={equipo}
          onClose={() => setTecnicoSeleccionado(null)}
        />
      )}
    </div>
  );
}
