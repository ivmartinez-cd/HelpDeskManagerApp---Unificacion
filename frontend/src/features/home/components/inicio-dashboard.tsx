"use client";

import { useEffect, useState } from "react";
import { useSession } from "@/services/session-provider";
import { SegmentedControl } from "@/shared/components/ui/segmented-control";
import { quietCards } from "../config/card-quiet";
import {
  VIEWS,
  cardsDeVista,
  layoutVisible,
  moduleAccessFrom,
  type ViewKey,
} from "../config/dashboard-registry";
import { buildKpiTiles } from "../config/kpi-tiles";
import { useDashboardData } from "../hooks/use-dashboard-data";
import { useNow } from "../hooks/use-now";
import { fechaLarga, textoHace } from "../utils/inicio-format";
import { AccesosDirectos } from "./accesos-directos";
import { CardSlot } from "./card-slot";
import { DashboardGrid } from "./dashboard-grid";
import { KpiStrip } from "./kpi-strip";
import { QuietStrip } from "./quiet-strip";

const VISTA_STORAGE_KEY = "inicio.vista";

/** Última vista elegida, por navegador (conveniencia, no preferencia de
 * cuenta). Se lee después del montaje para no desincronizar el SSR. */
function useVistaPersistida(): [ViewKey, (v: ViewKey) => void] {
  const [vista, setVista] = useState<ViewKey>("hoy");
  useEffect(() => {
    try {
      const guardada = window.localStorage.getItem(VISTA_STORAGE_KEY);
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (VIEWS.some((v) => v.key === guardada)) setVista(guardada as ViewKey);
    } catch {
      // Sin storage (modo privado, bloqueo): se queda en "hoy".
    }
  }, []);
  const elegir = (v: ViewKey) => {
    setVista(v);
    try {
      window.localStorage.setItem(VISTA_STORAGE_KEY, v);
    } catch {
      // idem
    }
  };
  return [vista, elegir];
}

/** Dashboard de Inicio (rediseño 2026-08-22, ver
 * docs/MASTER_PROMPT_REDISENO_DASHBOARD_INICIO.md). Una sola pantalla sin
 * scroll de página: encabezado (título + fecha + accesos), franja de KPIs
 * siempre visible, y dos vistas del grid de viewport fijo — "Hoy" (lo que se
 * opera en el día) y "Seguimiento" (lo que se mira cada tanto). Los paneles
 * sin novedades bajan a una tira al pie y los demás se agrandan. Qué card va
 * dónde lo dice `VIEWS` en dashboard-registry.ts; qué datos recibe cada una,
 * `CardSlot`. Este componente solo compone. */
export function InicioDashboard() {
  const { modules, hasFeature } = useSession();
  const access = moduleAccessFrom(modules, hasFeature);
  const data = useDashboardData(access);
  const now = useNow(30_000);
  const [vista, setVista] = useVistaPersistida();

  const quiet = quietCards(data);
  const rows = layoutVisible(vista, access, new Set(quiet.keys()));
  const sinNovedades = cardsDeVista(vista, access)
    .map((id) => quiet.get(id))
    .filter((q) => q !== undefined);
  const tiles = buildKpiTiles(data, access);
  const vistasDisponibles = VIEWS.filter((v) => cardsDeVista(v.key, access).length > 0);

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

      {vistasDisponibles.length > 1 && (
        <div className="flex flex-none items-center">
          <SegmentedControl
            label="Vista"
            size="sm"
            value={vista}
            onChange={(v) => setVista(v as ViewKey)}
            options={vistasDisponibles.map((v) => ({ value: v.key, label: v.label }))}
          />
        </div>
      )}

      <DashboardGrid rows={rows} render={(id) => <CardSlot id={id} data={data} access={access} />} />

      <QuietStrip items={sinNovedades} />
    </div>
  );
}
