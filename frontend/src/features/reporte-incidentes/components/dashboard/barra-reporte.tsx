"use client";

import { useMemo, useState } from "react";
import { CalendarDays, Loader2 } from "lucide-react";
import type { EstadoDashboard } from "../../hooks/use-reporte";
import { etiquetaPeriodo, mesesEntre, periodosRecientes } from "../../lib/periodos";
import { SelectorRango } from "../seleccion/selector-rango";
import { desdeInicial, esPreset, etiquetaRango, periodoMenos, textoMeses } from "../seleccion/rango";
import { CONTROL, ETIQUETA } from "../seleccion/estilos";

/** Mes final + rango del dashboard (port de `Toolbar` del legacy, sin el
 * cliente ni el PDF, que van en el encabezado). Todo cambio navega. */
export function BarraReporte({ estado }: { estado: EstadoDashboard }) {
  const { pedido, reporte } = estado;
  const opcionesMes = useMemo(() => periodosRecientes(24), []);
  // "Desde" fijado por el usuario en modo Personalizado.
  const [desdeElegido, setDesdeElegido] = useState<string | null>(null);

  if (!pedido) return null;
  const hasta = pedido.periodo || opcionesMes[0] || "";
  const { meses } = pedido;
  const opcionesDesde = opcionesMes.filter((p) => p <= hasta);
  // Si se llegó por URL con un rango que no es preset, se infiere el "Desde".
  const desde =
    desdeElegido && opcionesDesde.includes(desdeElegido)
      ? desdeElegido
      : !esPreset(meses)
        ? periodoMenos(hasta, meses - 1)
        : null;
  const ocupado = estado.navegando || estado.cargando || estado.actualizando;

  function aplicarDesde(nuevo: string) {
    setDesdeElegido(nuevo);
    estado.cambiarRango(hasta, mesesEntre(nuevo, hasta));
  }

  /** Con preset la ventana se desplaza; en Personalizado el "Desde" queda
   * clavado y se recalculan los meses (si quedaría al revés, colapsa a 1). */
  function aplicarHasta(nuevo: string) {
    if (!desde) return estado.cambiarRango(nuevo, meses);
    if (desde > nuevo) {
      setDesdeElegido(null);
      return estado.cambiarRango(nuevo, 1);
    }
    setDesdeElegido(desde);
    estado.cambiarRango(nuevo, mesesEntre(desde, nuevo));
  }

  return (
    <fieldset
      disabled={estado.navegando}
      className="flex flex-wrap items-center gap-x-4 gap-y-3 rounded-[12px] border border-border bg-card px-4 py-3"
    >
      <label className="flex items-center gap-2">
        <span className={ETIQUETA}>Hasta</span>
        <select className={CONTROL} value={hasta} onChange={(e) => aplicarHasta(e.target.value)}>
          {opcionesMes.map((p) => (
            <option key={p} value={p}>
              {etiquetaPeriodo(p)}
            </option>
          ))}
        </select>
      </label>
      <SelectorRango
        size="sm"
        meses={meses}
        desde={desde}
        opcionesDesde={opcionesDesde}
        onPreset={(n) => {
          setDesdeElegido(null);
          estado.cambiarRango(hasta, n);
        }}
        onPersonalizado={() => aplicarDesde(desde ?? desdeInicial(opcionesDesde, hasta))}
        onDesde={aplicarDesde}
      />
      <span className="inline-flex items-center gap-1.5 font-body text-[13px] text-muted-foreground">
        <CalendarDays className="h-3.5 w-3.5" aria-hidden="true" />
        {reporte?.rango_etiqueta ?? etiquetaRango(hasta, meses)}
        {meses > 1 && ` · ${textoMeses(meses)}`}
      </span>
      <span
        className="ml-auto inline-flex items-center gap-1.5 font-body text-xs text-muted-foreground"
        aria-live="polite"
      >
        {ocupado && <Loader2 className="h-3.5 w-3.5 animate-spin text-brand-orange" aria-hidden="true" />}
        {ocupado ? "Generando reporte…" : ""}
      </span>
    </fieldset>
  );
}
