"use client";

import { textoDesdeSync } from "@/features/contadores/utils/calendario-format";
import { useSession } from "@/services/session-provider";
import {
  useCalendarioHome,
  useContadoresResumen,
  useInsumosDashboard,
  useLiquidacionesPendientes,
  useParqueResumen,
  usePendientesResumen,
  useSlaHistoria,
  useTurnosHoy,
} from "../hooks/use-inicio-data";
import { buildKpis } from "../utils/build-kpis";
import { CARDS, COLUMNS, cardsForCol, type ColKey, type ModuleAccess } from "../config/dashboard-registry";
import { ClientesHoyCard } from "./clientes-hoy-card";
import { ContadoresDonutCard } from "./contadores-donut-card";
import { HeatmapSemanaCard } from "./heatmap-semana-card";
import { InsumosSinCargarCard } from "./insumos-sin-cargar-card";
import { KpiStrip } from "./kpi-strip";
import { LiquidacionesPendientesCard } from "./liquidaciones-pendientes-card";
import { ParqueDonutCard } from "./parque-donut-card";
import { PendientesAntiguedadCard } from "./pendientes-antiguedad-card";
import { PendientesACerrarCard } from "@/features/sla/components/pendientes-a-cerrar-card";
import { SlaMesCard } from "./sla-mes-card";
import { TurnosTimelineCard } from "./turnos-timeline-card";

function fechaHoy(): string {
  const texto = new Date().toLocaleDateString("es-AR", { weekday: "long", day: "numeric" });
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

/** Dashboard de Inicio. El orden y columna de cada card se declara en
 * dashboard-registry.ts — este componente solo renderiza lo que el registro
 * indica. Para mover una card: editar el registro, no este archivo. */
export function InicioDashboard() {
  const { modules } = useSession();

  const access: ModuleAccess = {
    contadores:   modules.some((m) => m.key === "contadores"),
    sla:          modules.some((m) => m.key === "sla"),
    prestadores:  modules.some((m) => m.key === "prestadores"),
    insumos:      modules.some((m) => m.key === "insumos"),
    liquidaciones: modules.some((m) => m.key === "liquidaciones"),
  };

  const turnos            = useTurnosHoy();
  const calendario        = useCalendarioHome(access.contadores);
  const contadoresResumen = useContadoresResumen(access.contadores);
  const slaHistoria       = useSlaHistoria(access.sla);
  const parque            = useParqueResumen(access.prestadores);
  const pendientesResumen = usePendientesResumen(access.sla);
  const insumosDashboard  = useInsumosDashboard(access.insumos);
  const liquidacionesPendientes = useLiquidacionesPendientes(access.liquidaciones);

  const kpis = buildKpis({
    prestadores: access.prestadores,
    contadores:  access.contadores,
    sla:         access.sla,
    parque,
    contadoresResumen,
    slaHistoria,
    calendario,
  });

  function renderCard(id: string) {
    switch (id) {
      case "turnos":
        return <TurnosTimelineCard shifts={turnos.data ?? []} loading={turnos.loading} error={turnos.error} />;
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
      case "sla-mes":
        return <SlaMesCard historia={slaHistoria.data} loading={slaHistoria.loading} error={slaHistoria.error} />;
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
      default:
        return null;
    }
  }

  return (
    <div className="flex h-full flex-col gap-3 px-7 py-4">
      <div className="flex flex-none flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-heading text-[25px] font-extrabold text-foreground">Inicio</h1>
          <p className="mt-0.5 font-body text-sm text-muted-foreground">
            Panel principal con turnos de operadores y planificación diaria.
          </p>
        </div>
        <div className="flex items-center gap-2 font-body text-[13px] text-muted-foreground">
          <span className="h-[7px] w-[7px] rounded-full bg-emerald-500 shadow-[0_0_0_3px_rgba(34,197,94,.15)]" />
          {fechaHoy()}
          {access.contadores && calendario.data && ` · ${textoDesdeSync(calendario.data.lastSyncedAt)}`}
        </div>
      </div>

      <div className="flex-none">
        <KpiStrip kpis={kpis} />
      </div>

      {/* xl:grid-cols mirrors COLUMNS fractions in dashboard-registry.ts */}
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-3 xl:grid-cols-[1.4fr_1fr_0.9fr_0.9fr]">
        {COLUMNS.map(({ key }) => {
          const cards = cardsForCol(key as ColKey, access);
          if (!cards.length) return null;
          return (
            <div key={key} className="flex min-h-0 min-w-0 flex-col gap-3 overflow-y-auto thin-scrollbar pb-3">
              {cards.map((card) => (
                <div key={card.id}>{renderCard(card.id)}</div>
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}
