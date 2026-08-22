"use client";

import { SlidersHorizontal } from "lucide-react";
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
import { useDashboardPrefs } from "../hooks/use-dashboard-prefs";
import { useNow } from "../hooks/use-now";
import { fechaLarga, textoHace } from "../utils/inicio-format";
import { AccesosDirectos } from "./accesos-directos";
import { CardSlot } from "./card-slot";
import { DashboardGrid } from "./dashboard-grid";
import { KpiStrip } from "./kpi-strip";
import { PersonalizarModal } from "./personalizar-modal";
import { QuietStrip } from "./quiet-strip";

/** Dashboard de Inicio (rediseño 2026-08-22, ver
 * docs/MASTER_PROMPT_REDISENO_DASHBOARD_INICIO.md). Una sola pantalla sin
 * scroll de página: encabezado (título + fecha + accesos + Personalizar),
 * franja de KPIs siempre visible, y dos vistas del grid de viewport fijo —
 * "Hoy" (lo que se opera en el día) y "Seguimiento" (lo que se mira cada
 * tanto). Los paneles sin novedades bajan a una tira al pie; los que el
 * usuario ocultó en Personalizar no se muestran. Qué card va dónde lo dice
 * `VIEWS` en dashboard-registry.ts; qué datos recibe cada una, `CardSlot`.
 * Este componente solo compone. */
export function InicioDashboard() {
  const { user, modules, hasFeature } = useSession();
  const access = moduleAccessFrom(modules, hasFeature);
  const data = useDashboardData(access);
  const now = useNow(30_000);
  const { prefs, cargadas, setOculto, setVistaInicial, restablecer } = useDashboardPrefs(user.id);
  const [vista, setVista] = useState<ViewKey>("hoy");
  const [personalizando, setPersonalizando] = useState(false);

  // Al cargar las preferencias, abrir con la vista elegida por el usuario.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (cargadas) setVista(prefs.vistaInicial);
  }, [cargadas, prefs.vistaInicial]);

  const quiet = quietCards(data);
  const fuera = new Set([...quiet.keys(), ...prefs.ocultos]);
  const rows = layoutVisible(vista, access, fuera);
  const sinNovedades = cardsDeVista(vista, access)
    .filter((id) => !prefs.ocultos.includes(id))
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
        <div className="flex flex-wrap items-center justify-end gap-1.5">
          <AccesosDirectos />
          <button
            type="button"
            onClick={() => setPersonalizando(true)}
            title="Elegir qué paneles ver y con qué vista abrir"
            className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-2.5 py-1 font-body text-[12px] font-semibold text-muted-foreground transition-colors hover:border-brand-orange/50 hover:text-brand-orange"
          >
            <SlidersHorizontal className="h-3.5 w-3.5" aria-hidden="true" />
            Personalizar
          </button>
        </div>
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

      <PersonalizarModal
        isOpen={personalizando}
        onClose={() => setPersonalizando(false)}
        access={access}
        prefs={prefs}
        onOculto={setOculto}
        onVistaInicial={setVistaInicial}
        onRestablecer={restablecer}
      />
    </div>
  );
}
