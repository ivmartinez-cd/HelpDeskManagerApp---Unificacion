"use client";

import { useState } from "react";
import { useSession } from "@/services/session-provider";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import {
  useCalendarioHome,
  useContadoresResumen,
  useInsumosDashboard,
  useLiquidacionesPendientes,
  useParqueResumen,
  usePendientesResumen,
  useProximosEquipo,
  useSlaHistoria,
  useTurnosHoy,
} from "../hooks/use-inicio-data";
import { COLUMNS, cardsForCol, type ColKey, type ModuleAccess } from "../config/dashboard-registry";
import { ClientesHoyCard } from "./clientes-hoy-card";
import { ContadoresDonutCard } from "./contadores-donut-card";
import { HeatmapSemanaCard } from "./heatmap-semana-card";
import { InsumosSinCargarCard } from "./insumos-sin-cargar-card";
import { LiquidacionesPendientesCard } from "./liquidaciones-pendientes-card";
import { ParqueDonutCard } from "./parque-donut-card";
import { CierreMensualCard } from "./cierre-mensual-card";
import { PendientesAntiguedadCard } from "./pendientes-antiguedad-card";
import { PendientesACerrarCard } from "@/features/sla/components/pendientes-a-cerrar-card";
import { ProximosEquipoCard } from "@/features/vacaciones/components/proximos-equipo-card";
import { SlaMesCard } from "./sla-mes-card";
import { TurnosTimelineCard } from "./turnos-timeline-card";

const COL_LABELS: Record<ColKey, string> = {
  planificacion: "Planificación",
  contadores: "Contadores",
  sla: "SLA",
  admin: "Administración",
};

/** Dashboard de Inicio. El orden y columna de cada card se declara en
 * dashboard-registry.ts — este componente solo renderiza lo que el registro
 * indica. Para mover una card: editar el registro, no este archivo.
 * Las columnas del registro se muestran como pestañas: cada una agrupa las
 * cards de una sección para que se vean grandes en vez de apretadas
 * lado a lado. */
export function InicioDashboard() {
  const { modules } = useSession();

  const access: ModuleAccess = {
    contadores:   modules.some((m) => m.key === "contadores"),
    sla:          modules.some((m) => m.key === "sla"),
    prestadores:  modules.some((m) => m.key === "prestadores"),
    insumos:      modules.some((m) => m.key === "insumos"),
    liquidaciones: modules.some((m) => m.key === "liquidaciones"),
    vacaciones:   modules.some((m) => m.key === "vacaciones"),
  };

  const columnasVisibles = COLUMNS
    .map((col) => ({ ...col, cards: cardsForCol(col.key, access) }))
    .filter((col) => col.cards.length > 0);

  const [activeTab, setActiveTab] = useState<ColKey>(
    () => columnasVisibles[0]?.key ?? COLUMNS[0].key,
  );
  const tabActual = columnasVisibles.some((c) => c.key === activeTab)
    ? activeTab
    : columnasVisibles[0]?.key;

  const turnos            = useTurnosHoy();
  const calendario        = useCalendarioHome(access.contadores);
  const contadoresResumen = useContadoresResumen(access.contadores);
  const slaHistoria       = useSlaHistoria(access.sla);
  const parque            = useParqueResumen(access.prestadores);
  const pendientesResumen = usePendientesResumen(access.sla);
  const insumosDashboard  = useInsumosDashboard(access.insumos);
  const liquidacionesPendientes = useLiquidacionesPendientes(access.liquidaciones);
  const proximosEquipo    = useProximosEquipo(access.vacaciones);

  function renderCard(id: string) {
    switch (id) {
      case "turnos":
        return (
          <TurnosTimelineCard
            shifts={turnos.data?.shifts ?? []}
            varianteActiva={turnos.data?.varianteActiva ?? null}
            loading={turnos.loading}
            error={turnos.error}
          />
        );
      case "clientes-hoy":
        return (
          <ClientesHoyCard
            eventos={calendario.data?.hoy ?? []}
            subtitulo={calendario.data?.subtituloHoy ?? "Planificación de Contadores"}
            operadores={calendario.data?.operadores ?? []}
            lastSyncedAt={calendario.data?.lastSyncedAt ?? null}
            loading={calendario.loading}
            error={calendario.error}
          />
        );
      case "heatmap-semana":
        return (
          <HeatmapSemanaCard
            eventos={calendario.data?.semana ?? []}
            operadores={calendario.data?.operadores ?? []}
            loading={calendario.loading}
            error={calendario.error}
          />
        );
      case "contadores-donut":
        return (
          <ContadoresDonutCard
            resumen={contadoresResumen.data}
            loading={contadoresResumen.loading}
            error={contadoresResumen.error}
            onResolved={contadoresResumen.refetch}
          />
        );
      case "pendientes-antig":
        return (
          <PendientesAntiguedadCard
            eventos={calendario.data?.pendientes ?? []}
            operadores={calendario.data?.operadores ?? []}
            loading={calendario.loading}
            error={calendario.error}
          />
        );
      case "cierre-mensual":
        return (
          <CierreMensualCard
            pendientes={calendario.data?.pendientes ?? []}
            resumen={contadoresResumen.data}
            loading={calendario.loading || contadoresResumen.loading}
            error={calendario.error ?? contadoresResumen.error}
          />
        );
      case "sla-mes":
        return (
          <SlaMesCard
            historia={slaHistoria.data}
            loading={slaHistoria.loading}
            error={slaHistoria.error}
            onSynced={slaHistoria.refetch}
          />
        );
      case "pendientes-cerrar":
        return (
          <PendientesACerrarCard
            resumen={pendientesResumen.data}
            loading={pendientesResumen.loading}
            error={pendientesResumen.error}
          />
        );
      case "liquidaciones":
        return (
          <LiquidacionesPendientesCard
            data={liquidacionesPendientes.data}
            loading={liquidacionesPendientes.loading}
            error={liquidacionesPendientes.error}
            onSynced={liquidacionesPendientes.refetch}
          />
        );
      case "parque":
        return <ParqueDonutCard resumen={parque.data} loading={parque.loading} error={parque.error} />;
      case "insumos":
        return (
          <InsumosSinCargarCard
            dashboard={insumosDashboard.data}
            loading={insumosDashboard.loading}
            error={insumosDashboard.error}
          />
        );
      case "proximos-equipo":
        return (
          <ProximosEquipoCard
            data={proximosEquipo.data}
            loading={proximosEquipo.loading}
            error={proximosEquipo.error}
          />
        );
      default:
        return null;
    }
  }

  const cardsTabActual = columnasVisibles.find((c) => c.key === tabActual)?.cards ?? [];

  return (
    <div className="flex h-full flex-col gap-3 px-7 py-4">
      <div className="flex-none">
        <h1 className="font-heading text-[25px] font-extrabold text-foreground">Inicio</h1>
        <p className="mt-0.5 font-body text-sm text-muted-foreground">
          Panel principal con turnos de operadores y planificación diaria.
        </p>
      </div>

      {columnasVisibles.length > 1 && (
        <div className="flex-none">
          <SegmentedControl
            label="Sección"
            value={tabActual ?? ""}
            onChange={(v) => setActiveTab(v as ColKey)}
            options={columnasVisibles.map((c) => ({ value: c.key, label: COL_LABELS[c.key] }))}
          />
        </div>
      )}

      <div className="grid min-h-0 flex-1 auto-rows-min items-start grid-cols-1 gap-3 overflow-y-auto thin-scrollbar pb-3 lg:grid-cols-2">
        {cardsTabActual.map((card) => (
          <div key={card.id}>{renderCard(card.id)}</div>
        ))}
      </div>
    </div>
  );
}
