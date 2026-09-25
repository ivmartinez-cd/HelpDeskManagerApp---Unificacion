"use client";

import { useMemo, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { CalendarDays, Search } from "lucide-react";
import { Button } from "@/shared/components/ui/button";
import type { Empresa } from "../../types/reporte";
import { etiquetaPeriodo, mesesEntre, periodosRecientes } from "../../lib/periodos";
import { urlReporte } from "../../lib/url-reporte";
import { BuscadorCliente } from "./buscador-cliente";
import { SelectorRango } from "./selector-rango";
import { desdeInicial, etiquetaRango, textoMeses } from "./rango";
import { CONTROL, ETIQUETA } from "./estilos";

/** Pantalla de selección (port de `app/seleccion` + `ClientPicker`): cliente,
 * mes final y rango; "Analizar" abre el dashboard con eso en la URL. */
export function SeleccionCliente() {
  const router = useRouter();
  const [navegando, startTransition] = useTransition();
  const [empresa, setEmpresa] = useState<Empresa | null>(null);
  const opcionesMes = useMemo(() => periodosRecientes(24), []);
  const [hasta, setHasta] = useState(() => opcionesMes[0] ?? "");
  const [mesesPreset, setMesesPreset] = useState(1);
  const [desdeElegido, setDesdeElegido] = useState<string | null>(null);

  // Solo se puede arrancar en o antes del mes final; si el mes final cambia y
  // deja el "Desde" afuera, se reacomoda al más viejo disponible (como el legacy).
  const opcionesDesde = useMemo(() => opcionesMes.filter((p) => p <= hasta), [opcionesMes, hasta]);
  const desde =
    desdeElegido && !opcionesDesde.includes(desdeElegido)
      ? (opcionesDesde[opcionesDesde.length - 1] ?? null)
      : desdeElegido;
  const meses = desde ? mesesEntre(desde, hasta) : mesesPreset;

  function analizar() {
    if (!empresa) return;
    startTransition(() => router.push(urlReporte({ empresaId: empresa.id, periodo: hasta, meses })));
  }

  return (
    <div className="flex flex-col gap-6 px-4 py-6 md:px-9 md:py-8">
      <div className="flex flex-col gap-1.5">
        <h1 className="font-heading text-[25px] font-extrabold text-foreground">Reporte de Incidentes</h1>
        <p className="font-body text-sm text-muted-foreground">Elegí el cliente y el período a analizar.</p>
      </div>

      <section className="w-full max-w-[1000px] rounded-[12px] border border-border bg-card">
        <div className="grid gap-10 p-6 md:p-8 xl:grid-cols-2">
          <div className="flex flex-col gap-3">
            <h2 className="font-heading text-base font-bold text-foreground">Cliente</h2>
            <BuscadorCliente onSeleccionar={setEmpresa} />
          </div>

          <div className="flex flex-col gap-5">
            <h2 className="font-heading text-base font-bold text-foreground">Período</h2>
            <label className="flex flex-col gap-1.5">
              <span className={ETIQUETA}>Mes final</span>
              <select className={CONTROL} value={hasta} onChange={(e) => setHasta(e.target.value)}>
                {opcionesMes.map((p) => (
                  <option key={p} value={p}>
                    {etiquetaPeriodo(p)}
                  </option>
                ))}
              </select>
            </label>
            <div className="flex flex-col gap-1.5">
              <span className={ETIQUETA}>Rango (hacia atrás desde el mes final)</span>
              <SelectorRango
                meses={meses}
                desde={desde}
                opcionesDesde={opcionesDesde}
                onPreset={(n) => {
                  setDesdeElegido(null);
                  setMesesPreset(n);
                }}
                onPersonalizado={() => setDesdeElegido((d) => d ?? desdeInicial(opcionesDesde, hasta))}
                onDesde={setDesdeElegido}
              />
            </div>
            <div className="flex items-center gap-3 rounded-[10px] bg-muted px-4 py-3.5">
              <CalendarDays className="h-[18px] w-[18px] flex-none text-brand-orange" aria-hidden="true" />
              <div>
                <p className="font-body text-sm font-bold text-foreground">
                  {etiquetaRango(hasta, meses)} · {textoMeses(meses)}
                </p>
                <p className="font-body text-xs text-muted-foreground">Solo incidentes resueltos o cerrados.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-end gap-4 border-t border-border px-6 py-4 md:px-8">
          {!empresa && (
            <span className="font-body text-[13px] text-muted-foreground">Elegí primero un cliente.</span>
          )}
          <Button onClick={analizar} disabled={!empresa} loading={navegando}>
            {!navegando && <Search className="h-4 w-4" aria-hidden="true" />}
            {navegando ? "Iniciando análisis…" : "Analizar"}
          </Button>
        </div>
      </section>
    </div>
  );
}
