"use client";

import { textoDesdeSync } from "@/features/contadores/utils/calendario-format";
import { useSession } from "@/services/session-provider";
import {
  useCalendarioHome,
  useContadoresResumen,
  useInsumosDashboard,
  useParqueResumen,
  usePendientesResumen,
  useSlaHistoria,
  useTurnosHoy,
} from "../hooks/use-inicio-data";
import { buildKpis } from "../utils/build-kpis";
import { ClientesHoyCard } from "./clientes-hoy-card";
import { ContadoresDonutCard } from "./contadores-donut-card";
import { HeatmapSemanaCard } from "./heatmap-semana-card";
import { InsumosSinCargarCard } from "./insumos-sin-cargar-card";
import { KpiStrip } from "./kpi-strip";
import { ParqueDonutCard } from "./parque-donut-card";
import { PendientesAntiguedadCard } from "./pendientes-antiguedad-card";
import { PendientesACerrarCard } from "@/features/sla/components/pendientes-a-cerrar-card";
import { SlaMesCard } from "./sla-mes-card";
import { TurnosTimelineCard } from "./turnos-timeline-card";

function fechaHoy(): string {
  const texto = new Date().toLocaleDateString("es-AR", { weekday: "long", day: "numeric" });
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

/** Dashboard de Inicio (design_handoff_inicio): franja KPI + grid
 * 1.4fr/1fr/1fr. Cada fuente se pide una sola vez acá y se reparte entre la
 * franja y las cards; el gating por módulo es el mismo que usa el sidebar. */
export function InicioDashboard() {
  const { modules } = useSession();
  const verContadores = modules.some((m) => m.key === "contadores");
  const verSla = modules.some((m) => m.key === "sla");
  const verPrestadores = modules.some((m) => m.key === "prestadores");
  const verInsumos = modules.some((m) => m.key === "insumos");

  const turnos = useTurnosHoy();
  const calendario = useCalendarioHome(verContadores);
  const contadoresResumen = useContadoresResumen(verContadores);
  const slaHistoria = useSlaHistoria(verSla);
  const parque = useParqueResumen(verPrestadores);
  const pendientesResumen = usePendientesResumen(verSla);
  const insumosDashboard = useInsumosDashboard(verInsumos);

  const kpis = buildKpis({
    prestadores: verPrestadores,
    contadores: verContadores,
    sla: verSla,
    parque,
    contadoresResumen,
    slaHistoria,
    calendario,
  });

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
          {verContadores && calendario.data && ` · ${textoDesdeSync(calendario.data.lastSyncedAt)}`}
        </div>
      </div>

      <div className="flex-none">
        <KpiStrip kpis={kpis} />
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-3 xl:grid-cols-[1.4fr_1fr_0.9fr_0.9fr]">
        <div className="flex min-h-0 min-w-0 flex-col gap-3 overflow-y-auto thin-scrollbar pb-3">
          <TurnosTimelineCard
            shifts={turnos.data ?? []}
            loading={turnos.loading}
            error={turnos.error}
          />
          {verContadores && (
            <ContadoresDonutCard
              resumen={contadoresResumen.data}
              loading={contadoresResumen.loading}
              error={contadoresResumen.error}
              onResolved={contadoresResumen.refetch}
            />
          )}
        </div>

        {verContadores && (
          <div className="flex min-h-0 min-w-0 flex-col gap-3 overflow-y-auto thin-scrollbar pb-3">
            <ClientesHoyCard
              eventos={calendario.data?.hoy ?? []}
              subtitulo={calendario.data?.subtituloHoy ?? "Planificación de Contadores"}
              operadores={calendario.data?.operadores ?? []}
              lastSyncedAt={calendario.data?.lastSyncedAt ?? null}
              loading={calendario.loading}
              error={calendario.error}
            />
            <HeatmapSemanaCard
              eventos={calendario.data?.semana ?? []}
              operadores={calendario.data?.operadores ?? []}
              loading={calendario.loading}
              error={calendario.error}
            />
            <PendientesAntiguedadCard
              eventos={calendario.data?.pendientes ?? []}
              operadores={calendario.data?.operadores ?? []}
              loading={calendario.loading}
              error={calendario.error}
            />
          </div>
        )}

        {verSla && (
          <div className="flex min-h-0 min-w-0 flex-col gap-3 overflow-y-auto thin-scrollbar pb-3">
            <SlaMesCard
              historia={slaHistoria.data}
              loading={slaHistoria.loading}
              error={slaHistoria.error}
            />
            <PendientesACerrarCard
              resumen={pendientesResumen.data}
              loading={pendientesResumen.loading}
              error={pendientesResumen.error}
            />
          </div>
        )}

        {(verPrestadores || verInsumos) && (
          <div className="flex min-h-0 min-w-0 flex-col gap-3 overflow-y-auto thin-scrollbar pb-3">
            {verPrestadores && (
              <ParqueDonutCard
                resumen={parque.data}
                loading={parque.loading}
                error={parque.error}
              />
            )}
            {verInsumos && (
              <InsumosSinCargarCard
                dashboard={insumosDashboard.data}
                loading={insumosDashboard.loading}
                error={insumosDashboard.error}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
