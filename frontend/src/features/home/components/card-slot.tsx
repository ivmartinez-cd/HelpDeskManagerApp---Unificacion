"use client";

import dynamic from "next/dynamic";
import { PendientesACerrarCard } from "@/features/sla/components/pendientes-a-cerrar-card";
import { ProximosEquipoCard } from "@/features/vacaciones/components/proximos-equipo-card";
import { WatiPendientesCard } from "@/features/wati/components/wati-pendientes-card";
import type { CardId, ModuleAccess } from "../config/dashboard-registry";
import type { DashboardData } from "../hooks/use-dashboard-data";
import { ClientesHoyCard } from "./clientes-hoy-card";
import { DashboardCardSkeleton } from "./dashboard-card-skeleton";
import { FacturacionSinCerrarCard } from "./facturacion-sin-cerrar-card";
import { InsumosSinCargarCard } from "./insumos-sin-cargar-card";
import { LiquidacionesPendientesCard } from "./liquidaciones-pendientes-card";
import { OperadoresCard } from "./operadores-card";
import { ParqueCard } from "./parque-card";
import { TurnosTimelineCard } from "./turnos-timeline-card";

// La única card que sigue tirando de chart.js (sparkline de tendencia) va
// code-split fuera del bundle inicial de /inicio, la ruta más transitada.
const SlaMesCard = dynamic(() => import("./sla-mes-card").then((m) => m.SlaMesCard), {
  ssr: false,
  loading: () => <DashboardCardSkeleton />,
});

/** Resuelve un `CardId` del registro a su componente con los datos que
 * necesita. Es el único lugar que conoce ambas cosas; el orquestador solo
 * itera el layout. */
export function CardSlot({
  id,
  data,
  access,
}: {
  id: CardId;
  data: DashboardData;
  access: ModuleAccess;
}) {
  const {
    turnos,
    calendario,
    contadoresResumen,
    pendientesPeriodo,
    slaHistoria,
    parque,
    pendientesResumen,
    insumosDashboard,
    liquidacionesPendientes,
    proximosEquipo,
    watiPendientes,
  } = data;

  switch (id) {
    case "turnos":
      return (
        <TurnosTimelineCard
          shifts={turnos.data?.shifts ?? []}
          varianteActiva={turnos.data?.varianteActiva ?? null}
          loading={turnos.loading}
          error={turnos.error}
          onRetry={turnos.refetch}
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
          onRetry={calendario.refetch}
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
    case "insumos":
      return (
        <InsumosSinCargarCard
          dashboard={insumosDashboard.data}
          loading={insumosDashboard.loading}
          error={insumosDashboard.error}
          onRetry={insumosDashboard.refetch}
        />
      );
    case "facturacion":
      return (
        <FacturacionSinCerrarCard
          pendientes={calendario.data?.pendientes ?? []}
          operadores={calendario.data?.operadores ?? []}
          resumen={contadoresResumen.data}
          pendientesPeriodoAnterior={pendientesPeriodo.data}
          pendientesPeriodoAnteriorLoading={pendientesPeriodo.loading}
          loading={calendario.loading}
          error={calendario.error}
          onRetry={calendario.refetch}
        />
      );
    case "operadores":
      return (
        <OperadoresCard
          resumen={contadoresResumen.data}
          resumenLoading={contadoresResumen.loading}
          resumenError={contadoresResumen.error}
          onResolved={contadoresResumen.refetch}
          mostrarOperadores={access.cardOperadores}
          semana={calendario.data?.semana ?? []}
          operadores={calendario.data?.operadores ?? []}
          loading={calendario.loading}
          error={calendario.error}
          onRetry={() => {
            calendario.refetch();
            contadoresResumen.refetch();
          }}
        />
      );
    case "sla-mes":
      return (
        <SlaMesCard
          historia={slaHistoria.data}
          loading={slaHistoria.loading}
          error={slaHistoria.error}
          onSynced={slaHistoria.refetch}
          onRetry={slaHistoria.refetch}
        />
      );
    case "pendientes-cerrar":
      return (
        <PendientesACerrarCard
          resumen={pendientesResumen.data}
          loading={pendientesResumen.loading}
          error={pendientesResumen.error}
          onRetry={pendientesResumen.refetch}
        />
      );
    case "liquidaciones":
      return (
        <LiquidacionesPendientesCard
          data={liquidacionesPendientes.data}
          loading={liquidacionesPendientes.loading}
          error={liquidacionesPendientes.error}
          onSynced={liquidacionesPendientes.refetch}
          onRetry={liquidacionesPendientes.refetch}
        />
      );
    case "proximos-equipo":
      return (
        <ProximosEquipoCard
          data={proximosEquipo.data}
          loading={proximosEquipo.loading}
          error={proximosEquipo.error}
          onRetry={proximosEquipo.refetch}
        />
      );
    case "parque":
      return (
        <ParqueCard
          resumen={parque.data}
          loading={parque.loading}
          error={parque.error}
          onRetry={parque.refetch}
        />
      );
    default:
      return null;
  }
}
