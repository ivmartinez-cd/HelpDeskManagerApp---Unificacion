"use client";

import { useState } from "react";
import { useSession } from "@/services/session-provider";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { cn } from "@/shared/utils/cn";
import { useAutoGrid } from "../hooks/use-auto-grid";
import { celdaDe } from "../utils/grid-packing";
import {
  useCalendarioHome,
  useClientesPendientesPeriodoAnterior,
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
import { AccesosDirectos } from "./accesos-directos";
import { MiTurnoBanner } from "./mi-turno-banner";
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
import { WatiPendientesCard } from "@/features/wati/components/wati-pendientes-card";
import { useWatiPendientes } from "@/features/wati/hooks/use-wati-pendientes";
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
    wati:         modules.some((m) => m.key === "wati"),
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
  const pendientesPeriodo = useClientesPendientesPeriodoAnterior(access.contadores);
  const slaHistoria       = useSlaHistoria(access.sla);
  const parque            = useParqueResumen(access.prestadores);
  const pendientesResumen = usePendientesResumen(access.sla);
  const insumosDashboard  = useInsumosDashboard(access.insumos);
  const liquidacionesPendientes = useLiquidacionesPendientes(access.liquidaciones);
  const proximosEquipo    = useProximosEquipo(access.vacaciones);
  const watiPendientes    = useWatiPendientes(access.wati);

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
            pendientesPeriodoAnterior={pendientesPeriodo.data}
            pendientesPeriodoAnteriorLoading={pendientesPeriodo.loading}
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
      case "wati-pendientes":
        return (
          <WatiPendientesCard
            resumen={watiPendientes.resumen}
            pendientes={watiPendientes.pendientes}
            loading={watiPendientes.loading}
            error={watiPendientes.error}
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
  const { containerRef, itemRefs, layout } = useAutoGrid(cardsTabActual.length);

  return (
    <div className="flex h-full flex-col gap-3 px-7 py-4">
      <div className="flex-none">
        <h1 className="font-heading text-[25px] font-extrabold text-foreground">Inicio</h1>
        <p className="mt-0.5 font-body text-sm text-muted-foreground">
          Panel principal con turnos de operadores y planificación diaria.
        </p>
      </div>

      <MiTurnoBanner shifts={turnos.data?.shifts ?? []} loading={turnos.loading} />
      <AccesosDirectos />

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

      {/* Grid auto-ajustable (use-auto-grid): columnas y reparto se eligen
          midiendo el alto disponible y el de cada card, para que la pestaña
          entre sin scroll en cualquier resolución. Las cards se colocan con
          grid-row/grid-column explícitos, así cambiar de reparto no las
          desmonta. Solo si ni con el máximo de columnas entra, aparece scroll. */}
      <div ref={containerRef} className="min-h-0 flex-1">
        <div
          className={cn(
            "grid h-full content-start items-start gap-3 overflow-y-auto thin-scrollbar",
            !layout.medido && "invisible",
          )}
          style={{ gridTemplateColumns: `repeat(${layout.cols}, minmax(0, 1fr))` }}
        >
          {cardsTabActual.map((card, i) => {
            const { col, row } = celdaDe(layout.sizes, i);
            return (
              <div key={card.id} ref={itemRefs[i]} style={{ gridColumn: col, gridRow: row }}>
                {renderCard(card.id)}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
