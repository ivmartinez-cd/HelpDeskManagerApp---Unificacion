"use client";

import { TrendChart } from "@/features/insumos/components/shared";
import { BrandModal } from "@/shared/components/ui/brand-modal";
import { KpiGrid, KpiTile } from "@/shared/components/ui/kpi-tile";
import type { EvolucionEquipo, EvolucionTecnico } from "../../types/bono-tecnicos";

const decimalFormat = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 2 });

const MESES = [
  "Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
];

function labelDe(periodo: number): string {
  const mes = periodo % 100;
  return MESES[mes - 1] ?? String(mes);
}

interface BonoTecnicoAnualModalProps {
  tecnico: EvolucionTecnico;
  equipo: EvolucionEquipo | null;
  onClose: () => void;
}

export function BonoTecnicoAnualModal({ tecnico, equipo, onClose }: BonoTecnicoAnualModalProps) {
  const labels = tecnico.puntos.map((p) => labelDe(p.periodo));

  return (
    <BrandModal isOpen title={tecnico.tecnico} onClose={onClose} widthPx={720}>
      <div className="flex flex-col gap-5">
        <KpiGrid>
          <KpiTile
            label="Puntaje promedio del año"
            value={
              tecnico.puntaje_promedio !== null
                ? decimalFormat.format(tecnico.puntaje_promedio)
                : "—"
            }
            tone="orange"
          />
          <KpiTile label="Incidentes atendidos" value={String(tecnico.incidentes_total)} />
          <KpiTile
            label="TV aprobadas"
            value={String(tecnico.tv_aprobadas_total)}
            hint={`de ${tecnico.tv_solicitadas_total} solicitadas`}
          />
        </KpiGrid>

        <TrendChart
          title="Puntaje mensual"
          subtitle="Comparado contra el promedio del equipo"
          labels={labels}
          values={tecnico.puntos.map((p) => p.puntaje)}
          seriesLabel={tecnico.tecnico}
          projection={equipo ? equipo.puntos.map((p) => p.puntaje) : null}
          projectionLabel="Promedio del equipo"
          heightPx={220}
          formatValue={(v) => decimalFormat.format(v)}
        />

        <TrendChart
          title="Tareas Varias (TV)"
          subtitle="Solicitadas vs. aprobadas"
          labels={labels}
          values={tecnico.puntos.map((p) => p.tv_solicitadas)}
          seriesLabel="Solicitadas"
          projection={tecnico.puntos.map((p) => p.tv_aprobadas)}
          projectionLabel="Aprobadas"
          heightPx={220}
        />
      </div>
    </BrandModal>
  );
}
