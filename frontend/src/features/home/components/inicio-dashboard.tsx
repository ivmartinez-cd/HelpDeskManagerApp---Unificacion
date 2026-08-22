"use client";

import { useSession } from "@/services/session-provider";
import { layoutVisible, moduleAccessFrom } from "../config/dashboard-registry";
import { buildKpiTiles } from "../config/kpi-tiles";
import { useDashboardData } from "../hooks/use-dashboard-data";
import { useNow } from "../hooks/use-now";
import { fechaLarga, textoHace } from "../utils/inicio-format";
import { AccesosDirectos } from "./accesos-directos";
import { CardSlot } from "./card-slot";
import { DashboardGrid } from "./dashboard-grid";
import { KpiStrip } from "./kpi-strip";

/** Dashboard de Inicio (rediseño 2026-08-22, ver
 * docs/MASTER_PROMPT_REDISENO_DASHBOARD_INICIO.md). Tres capas en una sola
 * pantalla sin scroll de página: encabezado (título + fecha + accesos),
 * franja de KPIs y el grid de viewport fijo con las cards. Qué card va dónde
 * lo dice `LAYOUT` en dashboard-registry.ts; qué datos recibe cada una,
 * `CardSlot`. Este componente solo compone. */
export function InicioDashboard() {
  const { modules, hasFeature } = useSession();
  const access = moduleAccessFrom(modules, hasFeature);
  const data = useDashboardData(access);
  const now = useNow(30_000);
  const rows = layoutVisible(access);
  const tiles = buildKpiTiles(data, access);

  return (
    <div className="flex flex-col gap-3 px-6 py-3.5 short:gap-2.5 short:px-5 short:py-2.5 xl:h-full">
      <div className="flex flex-none flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <div className="flex items-baseline gap-3">
          <h1 className="font-heading text-[22px] font-extrabold leading-none text-foreground short:text-[20px]">
            Inicio
          </h1>
          {/* Texto dependiente del reloj/locale del cliente: el SSR puede
              diferir (ICU del contenedor, segundos) — se acepta el del cliente. */}
          <p className="font-body text-[12.5px] text-muted-foreground" suppressHydrationWarning>
            {fechaLarga(now)}
            <span className="mx-1.5 opacity-50">·</span>
            actualizado {textoHace(data.refreshedAt.toISOString(), now.getTime())}
          </p>
        </div>
        <AccesosDirectos />
      </div>

      <KpiStrip tiles={tiles} />

      <DashboardGrid rows={rows} render={(id) => <CardSlot id={id} data={data} access={access} />} />
    </div>
  );
}
